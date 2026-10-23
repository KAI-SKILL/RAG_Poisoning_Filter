#!/usr/bin/env bash
# Isolated shell fixtures only: mock scheduler, mock Python, no network/GPU/model.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
FIXTURE="$(mktemp -d "$SCRIPT_DIR/.shell-fixture.XXXXXX")"
trap 'rm -rf -- "$FIXTURE"' EXIT
DATA="$FIXTURE/data"; PROJECT="$DATA/fixtureupi/project with spaces"
TOOLS="$PROJECT/generation/all_experiments"; BIN="$FIXTURE/bin"
mkdir -p -- "$TOOLS" "$BIN"
for script in uoa_environment.sh submit_all_slurm.sh run_all_interactive.sh slurm_all_scopes_job.sh; do
  bash -n "$SCRIPT_DIR/$script"
  cp -- "$SCRIPT_DIR/$script" "$TOOLS/$script"
done
# Test production control flow under an isolated data root without writing /data.
# No such replacement is made to the delivered scripts.
sed "s@/data@$DATA@g" "$SCRIPT_DIR/uoa_environment.sh" > "$TOOLS/uoa_environment.sh"
: > "$TOOLS/run_model_suite.py"; printf '{}\n' > "$TOOLS/experiment_registry.json"
cat > "$BIN/sbatch" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
count=0; [[ ! -f "$MOCK_STATE" ]] || read -r count < "$MOCK_STATE"
count=$((count+1)); printf '%s\n' "$count" > "$MOCK_STATE"
printf 'CALL=%s\n' "$count" >> "$MOCK_ARGS"
printf 'ARG=%s\n' "$@" >> "$MOCK_ARGS"
if [[ "${MOCK_SBATCH_MODE:-success}" == fail_second && "$count" == 2 ]]; then printf 'mock permission denied\n' >&2; exit 1; fi
if [[ "${MOCK_SBATCH_MODE:-success}" == uncertain ]]; then printf 'mock unexpected scheduler output\n'; exit 0; fi
printf '%s;fixturecluster\n' "$((1000+count))"
MOCK
cat > "$BIN/fake-python" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
printf 'CALL\n' >> "$MOCK_PY_ARGS"
printf 'ARG=%s\n' "$@" >> "$MOCK_PY_ARGS"
printf 'ENV_CUDA=%s\nENV_PROXY=%s\nENV_NO_PROXY=%s\nENV_HF_DISABLE_XET=%s\nENV_HOME=%s\nENV_TMP=%s\nENV_HF_CACHE=%s\n' "$CUDA_VISIBLE_DEVICES" "$https_proxy" "$NO_PROXY" "$HF_HUB_DISABLE_XET" "$HOME" "$TMPDIR" "$HF_HUB_CACHE" >> "$MOCK_PY_ARGS"
model=''; while (($#)); do if [[ "$1" == --model-key ]]; then model="$2"; break; fi; shift; done
[[ "$model" != "${MOCK_PY_FAIL_MODEL:-}" ]] || exit 9
exit 0
MOCK
cat > "$BIN/findmnt" <<'MOCK'
#!/usr/bin/env bash
printf 'TARGET FSTYPE SOURCE\nfixture fixturefs fixture-source\n'
MOCK
chmod +x "$BIN/sbatch" "$BIN/fake-python" "$BIN/findmnt"
export PATH="$BIN:$PATH" GROUP9_UPI=fixtureupi GROUP9_PROJECT_ROOT="$PROJECT"
export MOCK_STATE="$FIXTURE/state" MOCK_ARGS="$FIXTURE/sbatch.args" MOCK_PY_ARGS="$FIXTURE/python.args"
export GROUP9_PYTHON="$BIN/fake-python"
unset SLURM_JOB_ID CUDA_VISIBLE_DEVICES USER_ENV WORKDIR GROUP9_HF_ENV GROUP9_HF_WORKDIR GROUP9_HF_CACHE GROUP9_TMPDIR GROUP9_XDG_CACHE_HOME GROUP9_HF_HOME GROUP9_TORCH_HOME GROUP9_PIP_CACHE_DIR
PASS=0
passed() { PASS=$((PASS+1)); printf 'PASS %s\n' "$1"; }
contains() { rg -q -F -- "$2" "$1" || { printf 'Expected %s in %s\n' "$2" "$1" >&2; exit 1; }; }
absent() { if rg -q -F -- "$2" "$1"; then printf 'Unexpected %s in %s\n' "$2" "$1" >&2; exit 1; fi; }
status_is() { local expected="$1"; shift; local actual=0; "$@" > "$FIXTURE/case.out" 2> "$FIXTURE/case.err" || actual=$?; [[ "$actual" == "$expected" ]] || { cat "$FIXTURE/case.out" "$FIXTURE/case.err" >&2; printf 'Expected exit %s, got %s\n' "$expected" "$actual" >&2; exit 1; }; }
reset_scheduler() { rm -f -- "$MOCK_STATE" "$MOCK_ARGS"; export MOCK_SBATCH_MODE=success; }
for script in submit_all_slurm.sh run_all_interactive.sh; do status_is 0 bash "$TOOLS/$script" --help; done
passed 'bash syntax and help'
status_is 0 bash "$TOOLS/submit_all_slurm.sh" --record-dir "$DATA/fixtureupi/plan records"
contains "$FIXTURE/case.out" '12 required completion slots'
[[ ! -e "$DATA/fixtureupi/plan records" && ! -e "$MOCK_STATE" ]]
passed 'default plan makes no directories or scheduler calls; includes all 12 slots'
status_is 2 bash "$TOOLS/run_all_interactive.sh" --run --record-dir "$DATA/fixtureupi/no allocation"
[[ ! -e "$DATA/fixtureupi/no allocation" && ! -e "$MOCK_PY_ARGS" ]]
passed 'login-shell compute refused without Slurm GPU allocation'
reset_scheduler
status_is 0 bash "$TOOLS/submit_all_slurm.sh" --submit --resume --record-dir "$DATA/fixtureupi/sequential records"
[[ "$(cat "$MOCK_STATE")" == 3 ]]
contains "$MOCK_ARGS" 'ARG=afterany:1001'; contains "$MOCK_ARGS" 'ARG=afterany:1002'
contains "$MOCK_ARGS" "ARG=$PROJECT"; contains "$MOCK_ARGS" 'ARG=--resume'
absent "$MOCK_ARGS" 'ARG=--partition'; absent "$MOCK_ARGS" 'ARG=--account'
[[ "$(rg -c $'\tSUBMITTED\t' "$DATA/fixtureupi/sequential records/job_ids.tsv")" == 3 ]]
passed 'explicit submission records 3 numeric IDs; default afterany chain; spaces and default scheduler settings'
reset_scheduler
status_is 0 bash "$TOOLS/submit_all_slurm.sh" --submit --parallel --partition gpu --account fixture --qos standard --time 01:00:00 --record-dir "$DATA/fixtureupi/parallel"
absent "$MOCK_ARGS" 'ARG=--dependency'; contains "$MOCK_ARGS" 'ARG=--partition'; contains "$MOCK_ARGS" 'ARG=gpu'; contains "$MOCK_ARGS" 'ARG=01:00:00'
passed 'parallel mode and explicit site/resource options preserved'
reset_scheduler; export MOCK_SBATCH_MODE=fail_second
status_is 3 bash "$TOOLS/submit_all_slurm.sh" --submit --record-dir "$DATA/fixtureupi/failure"
[[ "$(cat "$MOCK_STATE")" == 2 ]]
contains "$DATA/fixtureupi/failure/job_ids.tsv" 'FAILED_OR_UNCERTAIN'; contains "$DATA/fixtureupi/failure/job_ids.tsv" 'NOT_SUBMITTED'
passed 'scheduler denial stops further submissions and preserves uncertain/nonstarted states'
reset_scheduler; export MOCK_SBATCH_MODE=uncertain
status_is 3 bash "$TOOLS/submit_all_slurm.sh" --submit --record-dir "$DATA/fixtureupi/uncertain"
[[ "$(cat "$MOCK_STATE")" == 1 ]]
contains "$DATA/fixtureupi/uncertain/job_ids.tsv" 'FAILED_OR_UNCERTAIN'
passed 'unparseable scheduler output is not treated as a valid queue ID or retried'
reset_scheduler
mv "$TOOLS/experiment_registry.json" "$TOOLS/experiment_registry.hidden"
status_is 2 bash "$TOOLS/submit_all_slurm.sh" --submit --record-dir "$DATA/fixtureupi/missing registry"
[[ ! -e "$MOCK_STATE" && ! -e "$DATA/fixtureupi/missing registry" ]]
mv "$TOOLS/experiment_registry.hidden" "$TOOLS/experiment_registry.json"
passed 'missing unified registry prevents submission with no E3-only fallback'
export GROUP9_TMPDIR="$FIXTURE/outside-data"
status_is 2 bash "$TOOLS/submit_all_slurm.sh" --submit --record-dir "$DATA/fixtureupi/unsafe override"
[[ ! -e "$MOCK_STATE" ]]; unset GROUP9_TMPDIR
passed 'explicit storage override outside data is refused before submission'
mkdir -p "$FIXTURE/spool"
cp "$TOOLS/slurm_all_scopes_job.sh" "$FIXTURE/spool/slurm_script"
export SLURM_JOB_ID=fixturejob CUDA_VISIBLE_DEVICES='0,1' SLURM_SUBMIT_DIR="$PROJECT" SLURM_CPUS_PER_TASK=4
ORIGINAL_HOME="$HOME"
# Standard inherited defaults must be redirected to data, never used under HOME or /tmp.
export TMPDIR=/tmp XDG_CACHE_HOME="$HOME/.cache" HF_HOME="$HOME/.cache/huggingface" HF_HUB_CACHE="$HOME/.cache/hub"
unset GROUP9_PROJECT_ROOT
status_is 0 bash "$FIXTURE/spool/slurm_script" qwen25_3b_gguf --resume
contains "$MOCK_PY_ARGS" "ARG=$TOOLS/run_model_suite.py"
contains "$MOCK_PY_ARGS" 'ARG=Q'; contains "$MOCK_PY_ARGS" 'ARG=E1'; contains "$MOCK_PY_ARGS" 'ARG=E2'; contains "$MOCK_PY_ARGS" 'ARG=E3'
contains "$MOCK_PY_ARGS" 'ENV_CUDA=0'; contains "$MOCK_PY_ARGS" 'ENV_PROXY=http://squid.auckland.ac.nz:3128'
contains "$MOCK_PY_ARGS" 'ENV_NO_PROXY=localhost,127.0.0.1,::1'; contains "$MOCK_PY_ARGS" 'ENV_HF_DISABLE_XET=1'
contains "$MOCK_PY_ARGS" "ENV_HOME=$ORIGINAL_HOME"; contains "$MOCK_PY_ARGS" "ENV_TMP=$DATA/fixtureupi/tmp"
contains "$MOCK_PY_ARGS" "ENV_HF_CACHE=$DATA/fixtureupi/cache/hf_models"
passed 'spooled payload resolves submit directory, all four scopes, one GPU and UoA environment without HOME changes'
export GROUP9_PROJECT_ROOT="$PROJECT"
rm -f "$MOCK_PY_ARGS"
status_is 0 bash "$TOOLS/run_all_interactive.sh" --run --record-dir "$DATA/fixtureupi/interactive"
[[ "$(rg -c '^CALL$' "$MOCK_PY_ARGS")" == 3 ]]
[[ "$(rg -c 'PROCESS_EXITED_ZERO_UNVERIFIED' "$DATA/fixtureupi/interactive/execution_status.tsv")" == 3 ]]
absent "$DATA/fixtureupi/interactive/execution_status.tsv" 'COMPLETE'
passed 'allocated sequential execution records three zero exits as unverified, never completed experiments'
export MOCK_PY_FAIL_MODEL=llama31_8b
status_is 1 bash "$TOOLS/run_all_interactive.sh" --run --record-dir "$DATA/fixtureupi/interactive failure"
contains "$DATA/fixtureupi/interactive failure/execution_status.tsv" 'FAILED_OR_PAUSED'
passed 'model payload failure produces a nonzero wrapper exit and failed/paused process record'
printf 'SHELL_FIXTURE_SUCCESS checks=%s; mock-only, no GPU/model/network/real Slurm invocation.\n' "$PASS"
