#!/usr/bin/env bash
set -euo pipefail

# Smoke checks for the original CityGaussian V1 branch.
# The official README says the original V1 code is in V1-Original.

ROOT_DIR="${ROOT_DIR:-$HOME/paper-reproduce-20261}"
REPO_DIR="${CITYGAUSSIAN_DIR:-$ROOT_DIR/third_party/CityGaussian}"
ENV_NAME="${ENV_NAME:-gspl}"
V1_BRANCH="${V1_BRANCH:-V1-Original}"

if ! command -v conda >/dev/null 2>&1; then
  # shellcheck disable=SC1091
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
fi

# shellcheck disable=SC1091
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$ENV_NAME"

cd "$REPO_DIR"
git fetch --all --prune

# AutoDL users often shallow-clone only the main branch for speed. In that
# case `git branch -r` will not show V1-Original until we fetch it explicitly.
if ! git show-ref --verify --quiet "refs/remotes/origin/${V1_BRANCH}"; then
  git fetch --depth 1 origin "${V1_BRANCH}" || true
fi

if git show-ref --verify --quiet "refs/remotes/origin/${V1_BRANCH}"; then
  git checkout "$V1_BRANCH"
elif git show-ref --verify --quiet "refs/remotes/origin/V1-original"; then
  git checkout "V1-original"
else
  echo "Cannot find V1 branch. Available remote branches:" >&2
  git branch -r >&2
  exit 1
fi

echo "[CityGaussian V1 smoke] current commit:"
git log --oneline -1

echo "[CityGaussian V1 smoke] checking expected entrypoints..."
test -f main.py || test -f train.py

echo "[CityGaussian V1 smoke] checking Python/CUDA..."
python - <<'PY'
import torch

print("torch:", torch.__version__)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device:", torch.cuda.get_device_name(0))
PY

if [ -f main.py ]; then
  python main.py --help | head -n 80 || true
elif [ -f train.py ]; then
  python train.py --help | head -n 80 || true
fi

echo "[CityGaussian V1 smoke] OK."
echo "Check the V1 branch README/scripts before long training; V1 and V2 command formats differ."
