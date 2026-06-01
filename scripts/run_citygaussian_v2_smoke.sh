#!/usr/bin/env bash
set -euo pipefail

# Smoke checks for CityGaussianV2 on the official main branch.
# This script intentionally avoids long training. It verifies that the repo,
# config files, Python entrypoints, CUDA, and key helper scripts are visible.

ROOT_DIR="${ROOT_DIR:-$HOME/paper-reproduce-20261}"
REPO_DIR="${CITYGAUSSIAN_DIR:-$ROOT_DIR/third_party/CityGaussian}"
ENV_NAME="${ENV_NAME:-gspl}"
CONFIG_NAME="${CONFIG_NAME:-citygsv2_lfls_sh2_trim}"

if ! command -v conda >/dev/null 2>&1; then
  # shellcheck disable=SC1091
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

cd "$REPO_DIR"
git checkout main

echo "[CityGaussianV2 smoke] current commit:"
git log --oneline -1

echo "[CityGaussianV2 smoke] checking files..."
test -f main.py
test -f "configs/${CONFIG_NAME}.yaml"
test -f utils/partition_citygs.py
test -f utils/train_citygs_partitions.py
test -f utils/merge_citygs_ckpts.py
test -f utils/gs2d_mesh_extraction.py

echo "[CityGaussianV2 smoke] checking Python/CUDA..."
python - <<'PY'
import torch

print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY

echo "[CityGaussianV2 smoke] printing main.py help..."
python main.py --help | head -n 80

echo "[CityGaussianV2 smoke] OK."
echo "After preparing data, a normal V2 run follows the official order:"
echo "  python main.py fit --config configs/${CONFIG_NAME}.yaml -n ${CONFIG_NAME}"
echo "  python utils/partition_citygs.py --config_path configs/${CONFIG_NAME}.yaml --force"
echo "  python utils/train_citygs_partitions.py -n ${CONFIG_NAME}"
echo "  python utils/merge_citygs_ckpts.py outputs/${CONFIG_NAME}"
