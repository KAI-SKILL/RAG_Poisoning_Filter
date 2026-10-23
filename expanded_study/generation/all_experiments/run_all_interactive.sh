#!/usr/bin/env bash
# UoA: this is an already-allocated Slurm-session entry, never SSH direct compute.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="${GROUP9_PROJECT_ROOT:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}"
RUN=0; RESUME=0; RECORD_DIR=''
usage() {
  cat <<'EOF'
Usage: bash generation/all_experiments/run_all_interactive.sh [options]
  --project-root PATH  Project under /data/<UPI>/
  --record-dir PATH    New /data/<UPI>/ process-log directory
  --run                Run all three model suites sequentially inside Slurm only
  --resume             Forward guarded resume for each model's Q/E1/E2/E3 suite
  --dry-run            Plan only (ordinary default)
All UoA compute requires Slurm. Without SLURM_JOB_ID and a GPU binding, --run stays
plan-only and exits nonzero. This script never calls sbatch or bypasses Slurm.
EOF
}
value() { (($# >= 2)) || { printf 'Missing value for %s\n' "$1" >&2; exit 2; }; }
while (($#)); do
  case "$1" in
    --project-root) value "$@"; PROJECT_ROOT="$2"; shift 2;;
    --record-dir) value "$@"; RECORD_DIR="$2"; shift 2;;
    --run) RUN=1; shift;;
    --resume) RESUME=1; shift;;
    --dry-run) RUN=0; shift;;
    -h|--help) usage; exit 0;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2;;
  esac
done
source "$SCRIPT_DIR/uoa_environment.sh"
uoa_resolve_paths
PAYLOAD="$PROJECT_ROOT/generation/all_experiments/slurm_all_scopes_job.sh"
[[ -n "$RECORD_DIR" ]] || RECORD_DIR="$PROJECT_ROOT/generation/all_experiments/interactive/$(date -u +%Y%m%dT%H%M%SZ)"
for field in "$PROJECT_ROOT" "$RECORD_DIR"; do [[ "$field" != *$'\n'* && "$field" != *$'\t'* && "$field" != *$'\r'* ]] || { printf 'TSV delimiters are not allowed in paths.\n' >&2; exit 2; }; done
MODELS=(qwen25_3b_gguf qwen3_8b llama31_8b)
uoa_print_environment_plan
printf 'Plan: three independent model suites, each Q/E1/E2/E3 in registry order; reuse one already-allocated GPU sequentially.\n'
for model in "${MODELS[@]}"; do COMMAND=(bash "$PAYLOAD" "$model"); ((RESUME == 0)) || COMMAND+=(--resume); printf '%s: ' "$model"; printf '%q ' "${COMMAND[@]}"; printf '\n'; done
if (( ! RUN )); then printf 'PLAN_ONLY: no directories, network, compute or job submissions.\n'; exit 0; fi
if [[ -z "${SLURM_JOB_ID:-}" || -z "${CUDA_VISIBLE_DEVICES:-}" || "${CUDA_VISIBLE_DEVICES:-}" == '-1' || "${CUDA_VISIBLE_DEVICES:-}" == 'NoDevFiles' ]]; then
  printf 'NO_SLURM_GPU_ALLOCATION: plan only. Obtain the documented Slurm GPU session; do not compute directly in SSH/login shell.\n' >&2; exit 2
fi
uoa_require_data_layout
uoa_export_environment
uoa_validate_storage_environment
RECORD_DIR="$(realpath -m -- "$RECORD_DIR")"
[[ "$RECORD_DIR" == "$DATA_ROOT/"* ]] || { printf 'Record directory must be under %s.\n' "$DATA_ROOT" >&2; exit 2; }
[[ -f "$ENTRY" && -f "$REGISTRY" && -f "$PAYLOAD" ]] || { printf 'Unified all-scopes entry/registry/payload missing; no E3-only fallback.\n' >&2; exit 2; }
[[ ! -e "$RECORD_DIR" ]] || { printf 'Refusing existing process record directory.\n' >&2; exit 2; }
mkdir -p -- "$RECORD_DIR"
LEDGER="$RECORD_DIR/execution_status.tsv"
printf 'model_key\tprocess_status\texit_code\tstarted_utc\tfinished_utc\tstdout_log\tstderr_log\n' > "$LEDGER"
STOP_SIGNAL=''; CHILD_PID=''; ANY_FAILURE=0
forward() { STOP_SIGNAL="$1"; [[ -z "$CHILD_PID" ]] || kill -s "$1" "$CHILD_PID" 2>/dev/null || true; }
trap 'forward USR1' USR1
trap 'forward TERM' TERM
trap 'forward INT' INT
for model in "${MODELS[@]}"; do
  out="$RECORD_DIR/$model.stdout.log"; err="$RECORD_DIR/$model.stderr.log"
  if [[ -n "$STOP_SIGNAL" ]]; then printf '%s\tNOT_STARTED_AFTER_SIGNAL\t\t\t\t\t\n' "$model" >> "$LEDGER"; continue; fi
  COMMAND=(bash "$PAYLOAD" "$model"); ((RESUME == 0)) || COMMAND+=(--resume)
  start="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; "${COMMAND[@]}" > "$out" 2> "$err" & CHILD_PID=$!
  printf 'RUNNING %s (Q/E1/E2/E3); log=%s\n' "$model" "$out"
  while true; do if wait "$CHILD_PID"; then status=0; break; else status=$?; kill -0 "$CHILD_PID" 2>/dev/null || break; fi; done
  CHILD_PID=''; finish="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if ((status == 0)); then label=PROCESS_EXITED_ZERO_UNVERIFIED; else label=FAILED_OR_PAUSED; ANY_FAILURE=1; fi
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$model" "$label" "$status" "$start" "$finish" "$out" "$err" >> "$LEDGER"
done
trap - USR1 TERM INT
printf 'Process records: %s\nThese are not complete-result claims; the collector must validate every one of the 12 slots.\n' "$LEDGER"
[[ -z "$STOP_SIGNAL" ]] || exit 3
exit "$ANY_FAILURE"
