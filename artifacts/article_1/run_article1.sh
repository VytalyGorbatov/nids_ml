#!/usr/bin/env bash
# ─── Article 1 — Full run set ───────────────────────────────────────────────
# "A Weakly Supervised Neural Risk-Scoring Method for Detecting Attacks Missed
#  by Signature-Based NIDS"
#
# Runs the 5 training runs that back the headline + design-justification tables,
# then computes per-epoch Snort-FN recovery (R@1/5/10%) for each via the offline
# driver. Single set only — NO seed variation (author handles seeds separately).
#
# Run set:
#   B0  Snort anchor          — computed, no training (recovers 0 FN by def.)
#   B2  teacher_copy_alerted  — supervised(alerted),  head_last_block, SSL init
#   M3  method_headlast_pu    — PU,                   head_last_block, SSL init   [HEADLINE]
#   B3  oracle_isattack       — supervised(is_attack),head_last_block, SSL init   [upper bound]
#   M1  full_backbone_pu      — PU,                   full,            SSL init   [trainability contrast]
#   A1  scratch_full_pu       — PU,                   full,            RANDOM init [SSL ablation, no --pretrained]
#
# Comparisons: B0→B2→M3→B3 (headline) | M3 vs M1 (trainability) | M1 vs A1 (SSL pretraining)
#
# cuda stability: runs sequentially, one at a time, foreground.
# Usage:  bash nids_ml/artifacts/article_1/run_article1.sh
# ────────────────────────────────────────────────────────────────────────────
set -uo pipefail

# ─── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"     # .../nids_ml
WS_ROOT="$(cd "$PKG_DIR/.." && pwd)"           # .../NeuralNetworks

PYTHON_BIN="/home/vhorbato/.pyvenv/bin/python3"  # full path to python binary (must have torch, sklearn, etc.)
PRETRAIN_CFG="artifacts/article_1/configs/pretrain_uonly_ssl.json"
PRETRAIN_DIR="artifacts/article_1/pretrain"
PRETRAIN=""
CFG_DIR="artifacts/article_1/configs"          # relative to PKG_DIR
RUNS_DIR="artifacts/article_1/runs"            # relative to PKG_DIR
BUDGETS="0.01,0.05,0.10"

# Run list: "config_basename:use_pretrained(1|0)"
RUNS=(
  "teacher_copy_alerted:1"
  "method_headlast_pu:1"
  "oracle_isattack:1"
  "full_backbone_pu:1"
  "scratch_full_pu:0"
)

# ─── Stage 1: shared U-only contrastive pretraining ────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ Stage 1  Shared U-only SSL pretraining (30 epochs)             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
mkdir -p "$PKG_DIR/$PRETRAIN_DIR"
PRETRAIN_MARKER="$(mktemp "${TMPDIR:-/tmp}/article1-pretrain-start.XXXXXX")"
( cd "$PKG_DIR" && "$PYTHON_BIN" classifier_creator.py \
    --config "$PRETRAIN_CFG" \
    --device cuda ) 2>&1 | tee "$PKG_DIR/$PRETRAIN_DIR/train.log"
pretrain_rc=${PIPESTATUS[0]}

if [[ $pretrain_rc -ne 0 ]]; then
  rm -f "$PRETRAIN_MARKER"
  echo "ERROR: Stage-1 pretraining failed (rc=$pretrain_rc)"
  exit "$pretrain_rc"
fi

pretrain_epoch=-1
for checkpoint in "$PKG_DIR/$PRETRAIN_DIR"/pretrain_epoch*.pt; do
  [[ -f "$checkpoint" ]] || continue
  [[ "$checkpoint" -nt "$PRETRAIN_MARKER" ]] || continue
  epoch="${checkpoint##*pretrain_epoch}"
  epoch="${epoch%.pt}"
  [[ "$epoch" =~ ^[0-9]+$ ]] || continue
  if (( 10#$epoch > pretrain_epoch )); then
    pretrain_epoch=$((10#$epoch))
    PRETRAIN="${checkpoint#"$PKG_DIR/"}"
  fi
done
rm -f "$PRETRAIN_MARKER"

if [[ -z "$PRETRAIN" ]]; then
  echo "ERROR: no new pretrained checkpoint found in $PKG_DIR/$PRETRAIN_DIR"
  exit 1
fi
echo "Using latest Stage-1 checkpoint: $PRETRAIN (epoch $pretrain_epoch)"

# ─── B0: Snort anchor (computed, no training) ───────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║ B0  Snort anchor (reference — recovers 0 of its own FN)        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
( cd "$PKG_DIR" && "$PYTHON_BIN" - <<'PY'
import json
from pathlib import Path
a = json.loads(Path("../sip-dataset/attack/test.json").read_text())["dataset"]
b = json.loads(Path("../sip-dataset/benign/test.json").read_text())["dataset"]
recs = a + b
tp = sum(1 for r in recs if r["is_attack"]==1 and r["alerted"]==1)
fn = sum(1 for r in recs if r["is_attack"]==1 and r["alerted"]==0)
fp = sum(1 for r in recs if r["is_attack"]==0 and r["alerted"]==1)
tn = sum(1 for r in recs if r["is_attack"]==0 and r["alerted"]==0)
recall = tp/(tp+fn) if (tp+fn) else 0.0
prec   = tp/(tp+fp) if (tp+fp) else 0.0
print(f"  Snort TP={tp}  FN={fn}  FP={fp}  TN={tn}")
print(f"  Snort recall(is_attack)={recall:.4f}  precision={prec:.4f}")
print(f"  Snort-FN recovery R@1/5/10% = 0.0000 (by construction — these ARE Snort's misses)")
print(f"  Added benign FP over Snort = 0 (Snort baseline is the reference point)")
PY
) || echo "[warn] Snort anchor computation failed (non-fatal)"

# ─── Training runs + per-run offline R@FPR evaluation ───────────────────────
declare -a RESULTS=()
TOTAL=${#RUNS[@]}
PASS=0
FAIL=0
CAMP_START=$(date +%s)

idx=0
for entry in "${RUNS[@]}"; do
  name="${entry%%:*}"
  use_pt="${entry##*:}"
  idx=$((idx+1))

  echo ""
  echo "╔══════════════════════════════════════════════════════════════╗"
  echo "║ [$idx/$TOTAL] $name   (pretrained=$use_pt)"
  echo "║ $(date '+%Y-%m-%d %H:%M:%S')"
  echo "╚══════════════════════════════════════════════════════════════╝"

  run_dir="$RUNS_DIR/$name"
  mkdir -p "$PKG_DIR/$run_dir"
  start=$(date +%s)

  # ── Training (from PKG_DIR so ../sip-dataset and ./artifacts resolve) ──
  pt_args=()
  if [[ "$use_pt" == "1" ]]; then
    pt_args=(--pretrained "$PRETRAIN")
  fi
  ( cd "$PKG_DIR" && "$PYTHON_BIN" classifier_creator.py \
      --config "$CFG_DIR/$name.json" \
      "${pt_args[@]}" \
      --device cuda ) 2>&1 | tee "$PKG_DIR/$run_dir/train.log"
  train_rc=${PIPESTATUS[0]}

  if [[ $train_rc -ne 0 ]]; then
    echo "[FAIL] training failed for $name (rc=$train_rc)"
    RESULTS+=("FAIL  $name (train rc=$train_rc)")
    FAIL=$((FAIL+1))
    continue
  fi

  # ── Offline per-epoch R@FPR (from WS_ROOT so nids_ml imports) ──
  ( cd "$WS_ROOT" && "$PYTHON_BIN" -m nids_ml.artifacts.processors.epoch_budget_campaign \
      --run-dir "nids_ml/$run_dir" \
      --budgets "$BUDGETS" ) 2>&1 | tee "$PKG_DIR/$run_dir/epoch_budget.log"
  drv_rc=${PIPESTATUS[0]}

  end=$(date +%s); mins=$(( (end-start)/60 ))

  if [[ $drv_rc -ne 0 ]]; then
    echo "[WARN] driver failed for $name (rc=$drv_rc)"
    RESULTS+=("WARN  $name (train ok, driver rc=$drv_rc) [${mins}m]")
    FAIL=$((FAIL+1))
  else
    echo ""
    echo "── R@FPR matrix: $name ──"
    cat "$PKG_DIR/$run_dir/epoch_budget_matrix.md" 2>/dev/null || echo "(matrix not found)"
    RESULTS+=("OK    $name [${mins}m]")
    PASS=$((PASS+1))
  fi
done

# ─── Summary ────────────────────────────────────────────────────────────────
camp_mins=$(( ($(date +%s)-CAMP_START)/60 ))
echo ""
echo "════════════════════════════════════════════════════════════════"
echo " ARTICLE-1 RUN SET COMPLETE — $PASS ok, $FAIL failed, ${camp_mins}m"
echo "════════════════════════════════════════════════════════════════"
for r in "${RESULTS[@]}"; do echo "  $r"; done
echo ""
echo "Per-run R@1/5/10% tables:  $RUNS_DIR/*/epoch_budget_matrix.md"
echo "Headline progression:      Snort(B0) → teacher_copy(B2) → method(M3) → oracle(B3)"
echo "Ablations:                 M3 vs full_backbone(M1)  |  M1 vs scratch_full(A1)"
date
