#!/usr/bin/env bash
set -euo pipefail

# AutoDL setup script for CityGaussian / CityGaussianV2.
# It prepares the official repository and Python environment, but does not
# download large datasets or start long training jobs automatically.

ROOT_DIR="${ROOT_DIR:-$HOME/paper-reproduce-20261}"
WORK_DIR="${WORK_DIR:-$ROOT_DIR/third_party}"
REPO_DIR="${CITYGAUSSIAN_DIR:-$WORK_DIR/CityGaussian}"
ENV_NAME="${ENV_NAME:-gspl}"
CUDA_TAG="${CUDA_TAG:-cu118}"
PYTHON_VERSION="${PYTHON_VERSION:-3.9}"
REPO_URL="${REPO_URL:-https://github.com/Linketic/CityGaussian.git}"

echo "[CityGaussian setup] root: $ROOT_DIR"
echo "[CityGaussian setup] work dir: $WORK_DIR"
echo "[CityGaussian setup] repo dir: $REPO_DIR"
echo "[CityGaussian setup] conda env: $ENV_NAME"
echo "[CityGaussian setup] cuda tag: $CUDA_TAG"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required but not found. Please install git first." >&2
  exit 1
fi

if ! command -v conda >/dev/null 2>&1; then
  if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1091
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
  elif [ -f "/root/miniconda3/etc/profile.d/conda.sh" ]; then
    # shellcheck disable=SC1091
    source "/root/miniconda3/etc/profile.d/conda.sh"
  else
    echo "conda is required but not found. AutoDL images usually include conda; please activate it first." >&2
    exit 1
  fi
fi

mkdir -p "$WORK_DIR"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "[CityGaussian setup] cloning official repository..."
  git clone "$REPO_URL" "$REPO_DIR"
else
  echo "[CityGaussian setup] repository already exists, fetching updates..."
  git -C "$REPO_DIR" fetch --all --prune
fi

if ! conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "[CityGaussian setup] creating conda env $ENV_NAME..."
  conda create -y -n "$ENV_NAME" "python=$PYTHON_VERSION" pip
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

python -m pip install --upgrade pip setuptools wheel

cd "$REPO_DIR"
git checkout main

case "$CUDA_TAG" in
  cu118)
    TORCH_REQ="requirements/pyt201_cu118.txt"
    ;;
  *)
    echo "Unsupported CUDA_TAG=$CUDA_TAG. The official docs currently provide pyt201_cu118.txt; set CUDA_TAG=cu118." >&2
    exit 1
    ;;
esac

if [ -f "$TORCH_REQ" ]; then
  echo "[CityGaussian setup] installing PyTorch requirements: $TORCH_REQ"
  python -m pip install -r "$TORCH_REQ"
else
  echo "Cannot find $TORCH_REQ in $REPO_DIR" >&2
  exit 1
fi

echo "[CityGaussian setup] installing common requirements..."
python -m pip install -r requirements.txt

echo "[CityGaussian setup] installing CityGaussian requirements..."
python -m pip install -r requirements/CityGS.txt

echo "[CityGaussian setup] verifying imports and GPU..."
python - <<'PY'
import sys
import torch

print("python:", sys.version)
print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("cuda device:", torch.cuda.get_device_name(0))
PY

echo "[CityGaussian setup] done."
echo "Next:"
echo "  conda activate $ENV_NAME"
echo "  cd $REPO_DIR"
echo "  bash $ROOT_DIR/scripts/run_citygaussian_v2_smoke.sh"
