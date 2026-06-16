#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="/Users/vhorbato/.venv/bin/python"
PRETRAIN="artifacts/pretrain_epoch29.pt"

run_cfg() {
  local cfg="$1"
  echo "=================================================="
  echo "Running config: $cfg"
  echo "=================================================="
  "$PYTHON_BIN" classifier_creator.py --config "$cfg" --pretrained "$PRETRAIN"
}

run_cfg "artifacts/experiments/stage2_long_control_p020_ssl15_alert020.json"
run_cfg "artifacts/experiments/stage2_p024_ssl15_alert020_long.json"
run_cfg "artifacts/experiments/stage2_p028_ssl15_alert020_long.json"
run_cfg "artifacts/experiments/stage2_p016_ssl15_alert020_long.json"

echo "Campaign completed."
