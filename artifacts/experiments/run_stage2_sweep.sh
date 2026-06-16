#!/bin/zsh
set -euo pipefail
source /Users/vhorbato/.venv/bin/activate
cd /Users/vhorbato/Desktop/NeuralNetworks/nids_ml
PRETRAIN=/Users/vhorbato/Desktop/NeuralNetworks/nids_ml/artifacts/pretrain_epoch29.pt
configs=(
  artifacts/experiments/stage2_control_p020_ssl15_alert020.json
  artifacts/experiments/stage2_p020_ssl05_alert010.json
  artifacts/experiments/stage2_p020_ssl02_alert010.json
  artifacts/experiments/stage2_p020_ssl05_alert005.json
)
for cfg in ${configs[@]}; do
  echo Running "$cfg"
  /Users/vhorbato/.venv/bin/python classifier_creator.py --config "$cfg" --device mps --pretrained "$PRETRAIN"
done
