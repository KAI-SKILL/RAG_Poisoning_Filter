#!/usr/bin/env bash
# UoA plan by default; only explicit --submit invokes the user's sbatch command.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="${GROUP9_PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$(cd -- "$SCRIPT_DIR/../.." && pwd -P)}}"
PARTITION=''; ACCOUNT=''; QOS=''; SUBMIT=0; PARALLEL=0; RESUME=0; RECORD_DIR=''; WALLTIME='00:30:00'
usage() {
  cat <<'EOF'
Usage: bash generation/all_experiments/submit_all_slurm.sh [options]
  --project-root PATH  Unpacked project under /data/<UPI>/
  --partition NAME     Optional actual site GPU partition; otherwise Slurm default
  --account NAME       Optional actual Slurm account; otherwise Slurm default
  --qos NAME           Optional actual site QoS
  --time HH:MM:SS      Job time request (default official example: 00:30:00)
  --record-dir PATH    New /data/<UPI>/ directory for job_ids.tsv and CLI logs
  --parallel           Explicitly request independent concurrent jobs; default chain
  --resume             Forward guarded resume to the unified model-suite runner
  --submit             Submit three one-GPU model jobs; ordinary default is plan
  --dry-run            Plan only
Each model job runs Q, E1, E2 and E3 sequentially through run_model_suite.py. The three
models are chained with afterany by default. Submission is not experiment completion.
No password/token is requested, no HOME change, no login-node compute or paid API.
EOF
}
value() { (($# >= 2)) || { printf 'Missing value for %s\n' "$1" >&2; exit 2; }; }
while (($#)); do
  case "$1" in
    --project-root) value "$@"; PROJECT_ROOT="$2"; shift 2;;
    --partition) value "$@"; PARTITION="$2"; shift 2;;
    --account) value "$@"; ACCOUNT="$2"; shift 2;;
    --qos) value "$@"; QOS="$2"; shift 2;;
    --time) value "$@"; WALLTIME="$2"; shift 2;;
    --record-dir) value "$@"; RECORD_DIR="$2"; shift 2;;
    --parallel) PARALLEL=1; shift;;
    --resume) RESUME=1; shift;;
    --submit) SUBMIT=1; shift;;
    --dry-run) SUBMIT=0; shift;;
    -h|--help) usage; exit 0;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2;;
  esac
done
[[ "$WALLTIME" =~ ^([0-9]+-)?[0-9]+:[0-5][0-9]:[0-5][0-9]$ ]] || { printf 'Use a Slurm time value such as HH:MM:SS.\n' >&2; exit 2; }
source "$SCRIPT_DIR/uoa_environment.sh"
uoa_resolve_paths
PAYLOAD="$PROJECT_ROOT/generation/all_experiments/slurm_all_scopes_job.sh"
[[ -n "$RECORD_DIR" ]] || RECORD_DIR="$PROJECT_ROOT/generation/all_experiments/submissions/$(date -u +%Y%m%dT%H%M%SZ)"
for field in "$PROJECT_ROOT" "$RECORD_DIR" "$PARTITION" "$ACCOUNT" "$QOS"; do [[ "$field" != *$'\n'* && "$field" != *$'\t'* && "$field" != *$'\r'* ]] || { printf 'TSV delimiters are not allowed in paths/options.\n' >&2; exit 2; }; done
MODELS=(qwen25_3b_gguf qwen3_8b llama31_8b)
OPTIONS=(--parsable --chdir "$PROJECT_ROOT" --export=ALL --time "$WALLTIME")
[[ -z "$PARTITION" ]] || OPTIONS+=(--partition "$PARTITION")
[[ -z "$ACCOUNT" ]] || OPTIONS+=(--account "$ACCOUNT")
[[ -z "$QOS" ]] || OPTIONS+=(--qos "$QOS")
uoa_print_environment_plan
printf 'Plan: 3 model jobs x Q/E1/E2/E3 = 12 required completion slots. No E3-only fallback.\n'
printf 'Each job requests one GPU, four CPUs, 32 GiB RAM, time=%s (request, not a site-limit claim).\n' "$WALLTIME"
((PARALLEL)) && printf 'Scheduling: explicitly parallel.\n' || printf 'Scheduling: sequential afterany chain; failed/paused jobs remain incomplete.\n'
for index in 0 1 2; do
  COMMAND=(sbatch "${OPTIONS[@]}")
  if (( ! PARALLEL && index > 0 )); then COMMAND+=(--dependency 'afterany:<previous_job_id>'); fi
  COMMAND+=("$PAYLOAD" "${MODELS[$index]}"); ((RESUME == 0)) || COMMAND+=(--resume)
  printf '%s: ' "${MODELS[$index]}"; printf '%q ' "${COMMAND[@]}"; printf '\n'
done
if (( ! SUBMIT )); then printf 'PLAN_ONLY: no directories, installs, downloads, large-file hashing, compute or submissions. Use --submit explicitly on the UoA host.\n'; exit 0; fi
uoa_require_data_layout
uoa_export_environment
uoa_validate_storage_environment
RECORD_DIR="$(realpath -m -- "$RECORD_DIR")"
[[ "$RECORD_DIR" == "$DATA_ROOT/"* ]] || { printf 'Submission records must be under %s.\n' "$DATA_ROOT" >&2; exit 2; }
[[ -f "$ENTRY" && -f "$REGISTRY" && -f "$PAYLOAD" ]] || { printf 'Unified entry/registry/payload missing. No jobs submitted; no old E3-only fallback.\n' >&2; exit 2; }
command -v sbatch >/dev/null || { printf 'sbatch unavailable. No jobs submitted.\n' >&2; exit 2; }
[[ ! -e "$RECORD_DIR" ]] || { printf 'Refusing existing submission records: %s\n' "$RECORD_DIR" >&2; exit 2; }
mkdir -p -- "$RECORD_DIR"
LEDGER="$RECORD_DIR/job_ids.tsv"
printf 'model_key\tjob_id\tcluster\tsubmission_status\tstdout_log\tstderr_log\tdependency\n' > "$LEDGER"
append() { printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$@" >> "$LEDGER"; }
PREVIOUS=''
for index in 0 1 2; do
  model="${MODELS[$index]}"; out="$RECORD_DIR/$model.sbatch.stdout"; err="$RECORD_DIR/$model.sbatch.stderr"; dependency=''
  COMMAND=(sbatch "${OPTIONS[@]}")
  if (( ! PARALLEL )) && [[ -n "$PREVIOUS" ]]; then dependency="afterany:$PREVIOUS"; COMMAND+=(--dependency "$dependency"); fi
  COMMAND+=("$PAYLOAD" "$model"); ((RESUME == 0)) || COMMAND+=(--resume)
  if "${COMMAND[@]}" > "$out" 2> "$err"; then status=0; else status=$?; fi
  answer="$(tr -d '\r\n' < "$out")"; job_id=''; cluster=''
  if [[ "$answer" =~ ^([0-9]+)(\;[A-Za-z0-9_.-]+)?$ ]]; then job_id="${BASH_REMATCH[1]}"; [[ "$answer" != *';'* ]] || cluster="${answer#*;}"; fi
  if ((status == 0)) && [[ -n "$job_id" ]]; then
    append "$model" "$job_id" "$cluster" SUBMITTED "$out" "$err" "$dependency"
    PREVIOUS="$job_id"; printf 'SUBMITTED %s job_id=%s; no completion claim.\n' "$model" "$job_id"
  else
    append "$model" "$job_id" "$cluster" FAILED_OR_UNCERTAIN "$out" "$err" "$dependency"
    for ((later=index+1; later<3; later++)); do append "${MODELS[$later]}" '' '' NOT_SUBMITTED '' '' ''; done
    printf 'Failed/uncertain submission. Inspect %s; no retry or cancellation was automated.\n' "$LEDGER" >&2; exit 3
  fi
done
printf 'SUBMISSION_RECORDS_READY: %s\nOnly the collector can verify all 12 model/scope slots; queue IDs are not results.\n' "$LEDGER"
