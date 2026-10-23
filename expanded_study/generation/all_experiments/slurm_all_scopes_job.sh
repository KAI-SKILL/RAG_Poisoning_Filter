#!/usr/bin/env bash
#SBATCH --job-name=group9-suite
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:30:00
#SBATCH --signal=B:USR1@180
#SBATCH --output=group9-suite-%j.out
#SBATCH --error=group9-suite-%j.err
# Site partition/account defaults are left to Slurm unless explicitly overridden.
set -euo pipefail
MODEL_KEY="${1:-}"
case "$MODEL_KEY" in qwen25_3b_gguf|qwen3_8b|llama31_8b) ;; *) printf 'Specify one registered model key.\n' >&2; exit 2;; esac
shift
RESUME=0
for flag in "$@"; do case "$flag" in --resume) RESUME=1;; *) printf 'Unknown payload flag: %s\n' "$flag" >&2; exit 2;; esac; done
[[ -n "${SLURM_JOB_ID:-}" ]] || { printf 'UoA requires Slurm for all compute. This payload does not submit itself.\n' >&2; exit 2; }
PROJECT_ROOT="${GROUP9_PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-}}"
[[ -n "$PROJECT_ROOT" ]] || { printf 'Set GROUP9_PROJECT_ROOT or submit from the extracted project root.\n' >&2; exit 2; }
# Slurm runs a spool copy; do not locate the project through BASH_SOURCE here.
source "$PROJECT_ROOT/generation/all_experiments/uoa_environment.sh"
uoa_resolve_paths
uoa_require_data_layout
uoa_export_environment
uoa_validate_storage_environment
[[ -f "$ENTRY" && -f "$REGISTRY" ]] || { printf 'Unified all-scopes entry/registry is missing; no E3-only fallback is allowed.\n' >&2; exit 2; }
[[ -n "${CUDA_VISIBLE_DEVICES:-}" && "${CUDA_VISIBLE_DEVICES:-}" != '-1' && "${CUDA_VISIBLE_DEVICES:-}" != 'NoDevFiles' ]] || { printf 'No Slurm GPU binding. No model execution.\n' >&2; exit 2; }
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES%%,*}"
export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-4}"
export OPENBLAS_NUM_THREADS="$OMP_NUM_THREADS" MKL_NUM_THREADS="$OMP_NUM_THREADS"
mkdir -p -- "$TMPDIR" "$XDG_CACHE_HOME" "$HF_HOME" "$GROUP9_HF_CACHE" "$TORCH_HOME" "$PIP_CACHE_DIR"
printf 'Allocated job=%s; model=%s; scopes=Q,E1,E2,E3; one GPU binding=%s\n' "$SLURM_JOB_ID" "$MODEL_KEY" "$CUDA_VISIBLE_DEVICES"
if command -v findmnt >/dev/null; then findmnt -T "$DATA_ROOT" -o TARGET,FSTYPE,SOURCE || true; else printf 'findmnt unavailable; runtime must diagnose the actual filesystem.\n'; fi
printf 'Filesystem type above is observational; no local/NFS/Lustre type is assumed.\n'
BASE_PYTHON="${GROUP9_PYTHON:-python3}"
COMMAND=("$BASE_PYTHON" "$ENTRY" --project-root "$PROJECT_ROOT" --model-key "$MODEL_KEY" --scopes Q E1 E2 E3 --run)
((RESUME == 0)) || COMMAND+=(--resume)
exec "${COMMAND[@]}"
