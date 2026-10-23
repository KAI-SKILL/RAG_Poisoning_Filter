#!/usr/bin/env bash
# Functions only. Source from the plan/submission/payload shells; never edits HOME.
uoa_resolve_paths() {
  local requested_root="$PROJECT_ROOT"
  PROJECT_ROOT="$(realpath -m -- "$PROJECT_ROOT")"
  UPI="${GROUP9_UPI:-}"
  if [[ -z "$UPI" && "$requested_root" == /data/* ]]; then
    local relative="${requested_root#/data/}"
    UPI="${relative%%/*}"
  elif [[ -z "$UPI" && "$PROJECT_ROOT" == /data/* ]]; then
    local relative="${PROJECT_ROOT#/data/}"
    UPI="${relative%%/*}"
  fi
  DATA_ROOT="$(realpath -m -- "/data/${UPI:-<UPI>}")"
  ENTRY="$PROJECT_ROOT/generation/all_experiments/run_model_suite.py"
  REGISTRY="$PROJECT_ROOT/generation/all_experiments/experiment_registry.json"
}
uoa_require_data_layout() {
  [[ "$UPI" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && "$UPI" != '.' && "$UPI" != '..' ]] || { printf 'Set GROUP9_UPI or place the project under /data/<UPI>/.\n' >&2; return 2; }
  [[ "$PROJECT_ROOT" == "$DATA_ROOT" || "$PROJECT_ROOT" == "$DATA_ROOT/"* ]] || { printf 'UoA project must be under %s, not HOME or another location.\n' "$DATA_ROOT" >&2; return 2; }
}
uoa_export_environment() {
  export GROUP9_PROJECT_ROOT="$PROJECT_ROOT"
  export GROUP9_UPI="$UPI"
  export http_proxy='http://squid.auckland.ac.nz:3128'
  export https_proxy='http://squid.auckland.ac.nz:3128'
  export HTTP_PROXY="$http_proxy" HTTPS_PROXY="$https_proxy"
  export NO_PROXY='localhost,127.0.0.1,::1'
  export no_proxy="$NO_PROXY"
  export HF_HUB_DISABLE_XET=1
  # Ignore inherited HOME-/tmp-based standard cache defaults. Explicit Group9
  # overrides are validated below, so every persistent/temporary path stays in data.
  export XDG_CACHE_HOME="${GROUP9_XDG_CACHE_HOME:-$DATA_ROOT/cache/xdg}"
  export HF_HOME="${GROUP9_HF_HOME:-$DATA_ROOT/cache/huggingface}"
  export GROUP9_HF_CACHE="${GROUP9_HF_CACHE:-$DATA_ROOT/cache/hf_models}"
  export HF_HUB_CACHE="$GROUP9_HF_CACHE"
  export TORCH_HOME="${GROUP9_TORCH_HOME:-$DATA_ROOT/cache/torch}"
  export PIP_CACHE_DIR="${GROUP9_PIP_CACHE_DIR:-$DATA_ROOT/cache/pip}"
  export GROUP9_HF_ENV="${GROUP9_HF_ENV:-$DATA_ROOT/envs/group9_hf}"
  export USER_ENV="${USER_ENV:-$DATA_ROOT/envs/group9_native}"
  export WORKDIR="${WORKDIR:-$DATA_ROOT/work/group9_native}"
  export GROUP9_HF_WORKDIR="${GROUP9_HF_WORKDIR:-$DATA_ROOT/work/group9_hf}"
  export TMPDIR="${GROUP9_TMPDIR:-$DATA_ROOT/tmp}"
  export TMP="$TMPDIR" TEMP="$TMPDIR"
  export TOKENIZERS_PARALLELISM=false
}
uoa_validate_storage_environment() {
  local name path
  for name in XDG_CACHE_HOME HF_HOME GROUP9_HF_CACHE HF_HUB_CACHE TORCH_HOME PIP_CACHE_DIR GROUP9_HF_ENV USER_ENV WORKDIR GROUP9_HF_WORKDIR TMPDIR; do
    path="$(realpath -m -- "${!name}")"
    [[ "$path" == "$DATA_ROOT" || "$path" == "$DATA_ROOT/"* ]] || { printf '%s must be under %s; found %s\n' "$name" "$DATA_ROOT" "$path" >&2; return 2; }
    printf -v "$name" '%s' "$path"; export "$name"
  done
}
uoa_print_environment_plan() {
  printf 'UoA data root: %s\nProject: %s\n' "$DATA_ROOT" "$PROJECT_ROOT"
  printf 'Proxy: http://squid.auckland.ac.nz:3128; NO_PROXY=localhost,127.0.0.1,::1; HF_HUB_DISABLE_XET=1\n'
  printf 'Private env/cache/model/checkpoint/work/tmp paths stay under /data/<UPI>/. HOME is not changed.\n'
  printf 'Unified entry: %s\nRegistry: %s\n' "$ENTRY" "$REGISTRY"
}
