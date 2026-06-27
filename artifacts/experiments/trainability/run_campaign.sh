#!/usr/bin/env bash
# ─── Stage-2 Trainability Campaign ─────────────────────────────────────────
# Validates whether "1-epoch nnPU optimum" is genuine or a symptom of:
#   H1: LR too high for backbone  (run 3, 7)
#   H2: Prior shock pi_p          (run 5)
#   H3: Bad early-stop metric     (all runs — per-epoch R1/R5/R10)
#   H4: PU dominating SSL         (run 6)
#
# Runs sequentially (MPS stability). After each training run, the offline
# epoch-budget driver computes per-epoch Snort-FN recovery at FPR budgets.
#
# Usage:
#   cd nids_ml && bash artifacts/experiments/trainability/run_campaign.sh
#   # or to run only core (1-5):
#   cd nids_ml && bash artifacts/experiments/trainability/run_campaign.sh --core
# ────────────────────────────────────────────────────────────────────────────
set -uo pipefail

# ─── Configuration ─────────────────────────────────────
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="/Users/vhorbato/.venv/bin/python"
PRETRAIN="artifacts/pretrain/epoch29.pt"
CFG_DIR="artifacts/experiments/trainability"
BUDGETS="0.01,0.05,0.10"

# Core runs (must-have for hypothesis testing)
CORE_CONFIGS=(
  "$CFG_DIR/head_ep20.json"
  "$CFG_DIR/head_last_block_ep7.json"
  "$CFG_DIR/backbone_low_lr_ep7.json"
  "$CFG_DIR/full_ep7.json"
  "$CFG_DIR/full_pi020_ep7.json"
)

# Optional runs (H4 + second LR grid point)
OPT_CONFIGS=(
  "$CFG_DIR/full_ssl_up_ep7.json"
  "$CFG_DIR/backbone_low_lr_5x_ep7.json"
)

# Select run set
if [[ "${1:-}" == "--core" ]]; then
  CONFIGS=("${CORE_CONFIGS[@]}")
  echo "Mode: CORE only (5 runs)"
else
  CONFIGS=("${CORE_CONFIGS[@]}" "${OPT_CONFIGS[@]}")
  echo "Mode: FULL campaign (7 runs)"
fi

# Verify pretrain checkpoint exists
if [[ ! -f "$PRETRAIN" ]]; then
  echo "ERROR: pretrained checkpoint not found: $PRETRAIN"
  exit 1
fi

# ─── Run loop ──────────────────────────────────────────
declare -a RESULTS=()
TOTAL=${#CONFIGS[@]}
PASSED=0
FAILED=0
CAMPAIGN_START=$(date +%s)

for cfg in "${CONFIGS[@]}"; do
  name="$(basename "$cfg" .json)"
  idx=$((PASSED + FAILED + 1))

  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║ [$idx/$TOTAL] $name"
  echo "║ $(date '+%Y-%m-%d %H:%M:%S')"
  echo "╚══════════════════════════════════════════════════════════════╝"

  # Derive run_dir from the config's out_dir (extract via python for reliability)
  run_dir=$("$PYTHON_BIN" -c "import json; print(json.load(open('$cfg'))['artifacts']['out_dir'])")
  mkdir -p "$run_dir"

  start_ts=$(date +%s)

  # ── Training ──
  "$PYTHON_BIN" classifier_creator.py \
    --config "$cfg" \
    --pretrained "$PRETRAIN" \
    --device mps 2>&1 | tee "${run_dir}/train.log"
  train_rc=${PIPESTATUS[0]}

  if [[ $train_rc -ne 0 ]]; then
    echo "[FAIL] Training failed for $name (rc=$train_rc)"
    RESULTS+=("FAIL  $name: training error (rc=$train_rc)")
    ((FAILED++))
    continue
  fi

  # ── Offline epoch-budget evaluation ──
  "$PYTHON_BIN" -m nids_ml.artifacts.processors.epoch_budget_campaign \
    --run-dir "$run_dir" \
    --budgets "$BUDGETS" 2>&1 | tee "${run_dir}/epoch_budget.log"
  driver_rc=${PIPESTATUS[0]}

  end_ts=$(date +%s)
  elapsed=$(( end_ts - start_ts ))
  elapsed_min=$(( elapsed / 60 ))

  if [[ $driver_rc -ne 0 ]]; then
    echo "[WARN] epoch_budget_campaign failed for $name (rc=$driver_rc)"
    RESULTS+=("WARN  $name: train OK, driver error (rc=$driver_rc) [${elapsed_min}m]")
    ((FAILED++))
  else
    # Print the epoch-budget table inline for quick monitoring
    echo ""
    echo "── Results: $name ──"
    cat "${run_dir}/epoch_budget_matrix.md"
    echo ""
    echo "[OK] $name completed in ${elapsed_min}m ${elapsed}s"
    RESULTS+=("OK    $name [${elapsed_min}m]")
    ((PASSED++))
  fi
done

# ─── Campaign Summary ──────────────────────────────────
CAMPAIGN_END=$(date +%s)
CAMPAIGN_ELAPSED=$(( (CAMPAIGN_END - CAMPAIGN_START) / 60 ))

echo ""
echo "════════════════════════════════════════════════════════════════"
echo " TRAINABILITY CAMPAIGN COMPLETE"
echo " Total: $TOTAL | Passed: $PASSED | Failed: $FAILED"
echo " Wall time: ${CAMPAIGN_ELAPSED} min"
echo "════════════════════════════════════════════════════════════════"
for r in "${RESULTS[@]}"; do
  echo "  $r"
done
echo ""
echo "Per-epoch matrix files are in each run dir:"
echo "  artifacts/runs/phase3_trainability/*/epoch_budget_matrix.md"
echo ""
echo "To compare all runs, inspect R@5% column at each epoch across dirs."
date
