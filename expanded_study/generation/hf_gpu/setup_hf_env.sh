#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${GROUP9_PROJECT_ROOT:-$(cd -- "$SCRIPT_DIR/../.." && pwd)}"
ENV_DIR="${GROUP9_HF_ENV:-$PROJECT_ROOT/runtime_hf_env}"
PYTHON_BIN="${GROUP9_PYTHON:-python3}"
if [[ "${1:-}" == "--dry-run" ]]; then
  printf 'Private environment: %s\nPython: %s\nPyTorch: 2.7.1, official CUDA 12.6 wheel\n' "$ENV_DIR" "$PYTHON_BIN"
  printf 'This dry run installs nothing and starts no GPU job.\n'
  exit 0
fi
[[ $# -eq 0 ]] || { printf 'Usage: bash setup_hf_env.sh [--dry-run]\n' >&2; exit 2; }
"$PYTHON_BIN" -c 'import sys; assert (3,11)<=sys.version_info[:2]<(3,13), "Use Python 3.11 or 3.12 (GROUP9_PYTHON can select it)."'
if [[ ! -x "$ENV_DIR/bin/python" ]]; then "$PYTHON_BIN" -m venv "$ENV_DIR"; fi
"$ENV_DIR/bin/python" -m pip install 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cu126
"$ENV_DIR/bin/python" -m pip install -r "$SCRIPT_DIR/requirements.txt"
"$ENV_DIR/bin/python" -m pip freeze > "$ENV_DIR/resolved_requirements.txt"
"$ENV_DIR/bin/python" -c 'import torch,transformers,numpy; print("torch",torch.__version__,"wheel_cuda",torch.version.cuda,"transformers",transformers.__version__,"numpy",numpy.__version__); print("Environment ready; no model was loaded.")'
