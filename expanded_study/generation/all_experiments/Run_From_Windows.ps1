<#
.SYNOPSIS
Stage the complete Group9 package and explicitly submit its three UoA Slurm jobs.
.DESCRIPTION
Plan only by default. -UploadOnly performs ssh/scp/extraction without submission.
-Submit performs ssh/scp/extraction and calls submit_all_slurm.sh --submit.
Connect the university VPN first. OpenSSH handles host keys/password/2FA normally.
No password, token, credential download, GPU execution or paid API is in this script.
Requires Windows PowerShell 5.1+ or PowerShell 7, and Windows OpenSSH ssh/scp.
.EXAMPLE
.\Run_From_Windows.ps1 -UPI abc123 -Server 3 -ZipPath 'C:\Downloads\Group9_UoA_All_Experiments_2026-10-22.zip'
.EXAMPLE
.\Run_From_Windows.ps1 -UPI abc123 -Server 3 -ZipPath 'C:\Downloads\Group9_UoA_All_Experiments_2026-10-22.zip' -UploadOnly
.EXAMPLE
.\Run_From_Windows.ps1 -UPI abc123 -Server 3 -ZipPath 'C:\Downloads\Group9_UoA_All_Experiments_2026-10-22.zip' -Time '04:00:00' -Submit
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$')]
    [string]$UPI,
    [ValidateRange(1, 3)]
    [int]$Server = 3,
    [string]$ClusterHost = '',
    [string]$ZipPath = (Join-Path (Get-Location) 'Group9_UoA_All_Experiments_2026-10-22.zip'),
    [ValidatePattern('^([0-9]+-)?[0-9]+:[0-5][0-9]:[0-5][0-9]$')]
    [string]$Time = '00:30:00',
    [string]$Partition = '',
    [string]$Account = '',
    [string]$Qos = '',
    [string]$RemoteSetupFile = '',
    [switch]$Parallel,
    [switch]$UploadOnly,
    [switch]$Submit
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($UPI -eq '.' -or $UPI -eq '..') { throw 'Use your own actual UPI.' }
if ($Submit -and $UploadOnly) { throw 'Choose -Submit or -UploadOnly, not both.' }
foreach ($Option in @($Partition, $Account, $Qos)) {
    if ($Option -ne '' -and $Option -notmatch '^[A-Za-z0-9_.-]+$') {
        throw 'Partition/account/QoS must be the actual site identifier, with letters, digits, dot, underscore or hyphen.'
    }
}
$HostName = $ClusterHost
if ($HostName -eq '') { $HostName = Read-Host 'Cluster SSH hostname' }
if ($HostName -notmatch '^[A-Za-z0-9][A-Za-z0-9.-]*$') { throw 'Enter a valid cluster SSH hostname.' }
$Target = '{0}@{1}' -f $UPI, $HostName
$DataRoot = '/data/{0}' -f $UPI
$ProjectRoot = '{0}/Group9_All_Experiments' -f $DataRoot
$ArchiveName = 'Group9_UoA_All_Experiments_2026-10-22.zip'
$RemoteArchive = '{0}/{1}' -f $DataRoot, $ArchiveName
$RemoteUpload = '{0}/group9-upload-{1}.zip' -f $DataRoot, ([guid]::NewGuid().ToString('N'))
if ($RemoteSetupFile -ne '') {
    if (-not $RemoteSetupFile.StartsWith($DataRoot + '/', [StringComparison]::Ordinal) -or
        $RemoteSetupFile -notmatch '^[A-Za-z0-9_./ -]+$' -or
        ($RemoteSetupFile.Split('/') -contains '..')) {
        throw 'RemoteSetupFile must be your existing module/setup file under /data/<UPI>/, with no parent traversal.'
    }
}
function Quote-Bash([string]$Value) {
    if ($Value.Contains("'") -or $Value.Contains("`r") -or $Value.Contains("`n")) {
        throw 'Unexpected shell delimiter in an internally constructed remote value.'
    }
    return "'$Value'"
}
$SubmitArguments = @('--time', $Time)
if ($Partition -ne '') { $SubmitArguments += @('--partition', $Partition) }
if ($Account -ne '') { $SubmitArguments += @('--account', $Account) }
if ($Qos -ne '') { $SubmitArguments += @('--qos', $Qos) }
if ($Parallel) { $SubmitArguments += '--parallel' }
$SubmitArgumentText = ($SubmitArguments | ForEach-Object { Quote-Bash $_ }) -join ' '
Write-Host ('Host: {0}; your VPN/campus connection is required.' -f $Target)
Write-Host ('Local archive: {0}' -f $ZipPath)
Write-Host ('New project: {0}; existing project/archive will be refused.' -f $ProjectRoot)
Write-Host 'Scope: 3 models x Q/E1/E2/E3 = 12 required result slots.'
Write-Host ('Time request per model: {0}; the default 30 min is a documented example, not a completion or quota guarantee.' -f $Time)
if ($Parallel) { Write-Host 'Scheduling: explicitly parallel model jobs.' }
else { Write-Host 'Scheduling: afterany chain; one GPU at a time across the three model jobs.' }
if ($RemoteSetupFile -ne '') { Write-Host ('User-provided module/setup file: {0}' -f $RemoteSetupFile) }
Write-Host ('Submission command: bash generation/all_experiments/submit_all_slurm.sh --submit {0}' -f $SubmitArgumentText)
if (-not $Submit -and -not $UploadOnly) {
    Write-Host 'PLAN_ONLY: no network, upload, extraction or submission. Use -UploadOnly to stage, or -Submit to stage and submit.'
    return
}
foreach ($Executable in @('ssh', 'scp')) {
    if (-not (Get-Command $Executable -CommandType Application -ErrorAction SilentlyContinue)) {
        throw ('Windows OpenSSH {0} is unavailable. Install/enable the Windows OpenSSH Client using your normal IT process.' -f $Executable)
    }
}
$ResolvedZip = (Resolve-Path -LiteralPath $ZipPath).ProviderPath
if (-not (Test-Path -LiteralPath $ResolvedZip -PathType Leaf)) { throw 'ZipPath must be a local ZIP file.' }
if ([IO.Path]::GetFileName($ResolvedZip) -ne $ArchiveName) { throw ('Use the new complete package named {0}, not an older E3-only archive.' -f $ArchiveName) }
Add-Type -AssemblyName System.IO.Compression.FileSystem
$Archive = [IO.Compression.ZipFile]::OpenRead($ResolvedZip)
try {
    $Names = @()
    foreach ($Entry in $Archive.Entries) {
        $EntryName = $Entry.FullName.Replace('\', '/')
        if (-not $EntryName.StartsWith('Group9_All_Experiments/', [StringComparison]::Ordinal) -or
            ($EntryName.Split('/') -contains '..') -or $EntryName.Contains(':')) {
            throw ('Archive has an unexpected or unsafe path: {0}' -f $EntryName)
        }
        $Names += $EntryName
    }
    foreach ($Required in @('generation/all_experiments/submit_all_slurm.sh', 'generation/all_experiments/run_model_suite.py', 'generation/all_experiments/experiment_registry.json', 'generation/all_experiments/collect_all_results.py')) {
        if ($Names -cnotcontains ('Group9_All_Experiments/' + $Required)) { throw ('Complete package entry missing: {0}' -f $Required) }
    }
}
finally { $Archive.Dispose() }
$OriginalOutputEncoding = $OutputEncoding
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
function Invoke-RemoteBash([string]$ScriptText, [string]$Label) {
    # Remote values are fixed/validated; all multiline shell code goes over stdin.
    ($ScriptText.Replace("`r`n", "`n")) | & ssh -T -- $Target 'bash -s'
    if ($LASTEXITCODE -ne 0) { throw ('{0} failed (ssh exit {1}). Inspect its output; no automatic retry/cancel/overwrite was made.' -f $Label, $LASTEXITCODE) }
}
$RemoteValues = @'
UPI=__UPI__
DATA_ROOT=__DATA_ROOT__
PROJECT=__PROJECT_ROOT__
ARCHIVE=__REMOTE_ARCHIVE__
UPLOAD=__REMOTE_UPLOAD__
MODULE_SETUP=__MODULE_SETUP__
'@
$RemoteValues = $RemoteValues.Replace('__UPI__', (Quote-Bash $UPI)).Replace('__DATA_ROOT__', (Quote-Bash $DataRoot)).Replace('__PROJECT_ROOT__', (Quote-Bash $ProjectRoot)).Replace('__REMOTE_ARCHIVE__', (Quote-Bash $RemoteArchive)).Replace('__REMOTE_UPLOAD__', (Quote-Bash $RemoteUpload)).Replace('__MODULE_SETUP__', (Quote-Bash $RemoteSetupFile))
try {
    $Preflight = @'
set -euo pipefail
__VALUES__
[[ "$(id -un)" == "$UPI" ]] || { printf 'SSH account does not match the requested UPI.\n' >&2; exit 2; }
[[ -d "$DATA_ROOT" && -w "$DATA_ROOT" ]] || { printf 'Your /data/<UPI>/ directory is missing or not writable. Contact site support.\n' >&2; exit 2; }
for path in "$PROJECT" "$ARCHIVE" "$UPLOAD"; do
  [[ ! -e "$path" && ! -L "$path" ]] || { printf 'Refusing existing path: %s\n' "$path" >&2; exit 2; }
done
command -v unzip >/dev/null || { printf 'unzip unavailable; contact site support.\n' >&2; exit 2; }
if [[ -n "$MODULE_SETUP" ]]; then [[ -f "$MODULE_SETUP" ]] || { printf 'User module/setup file is missing.\n' >&2; exit 2; }; fi
printf 'Lightweight staging preflight passed; no model/build/download/GPU work performed.\n'
'@
    Invoke-RemoteBash ($Preflight.Replace('__VALUES__', $RemoteValues)) 'Remote staging preflight'
    & scp -- $ResolvedZip ('{0}:{1}' -f $Target, $RemoteUpload)
    if ($LASTEXITCODE -ne 0) { throw ('SCP upload failed (exit {0}). A partial uploaded ZIP may remain under your data directory; no job was submitted.' -f $LASTEXITCODE) }
    $Stage = @'
set -euo pipefail
__VALUES__
[[ ! -e "$PROJECT" && ! -L "$PROJECT" && ! -e "$ARCHIVE" && ! -L "$ARCHIVE" ]] || { printf 'Project/archive appeared after preflight; refusing to merge or overwrite.\n' >&2; exit 2; }
mv -n -- "$UPLOAD" "$ARCHIVE"
[[ ! -e "$UPLOAD" && -f "$ARCHIVE" ]] || { printf 'Archive could not be published without overwrite.\n' >&2; exit 2; }
unzip -q "$ARCHIVE" -d "$DATA_ROOT"
[[ -f "$PROJECT/generation/all_experiments/experiment_registry.json" && -f "$PROJECT/generation/all_experiments/run_model_suite.py" ]] || { printf 'Incomplete extracted package; no submission.\n' >&2; exit 2; }
printf 'STAGED: %s\nNo Slurm submission has been made by staging.\n' "$PROJECT"
'@
    Invoke-RemoteBash ($Stage.Replace('__VALUES__', $RemoteValues)) 'Remote extraction'
    if ($UploadOnly) {
        Write-Host 'UPLOAD_ONLY_COMPLETE: no jobs submitted. Follow the guide for user-owned model authorization/modules, then submit from the SSH terminal.'
        return
    }
    $Run = @'
set -euo pipefail
__VALUES__
if [[ -n "$MODULE_SETUP" ]]; then source "$MODULE_SETUP"; fi
export GROUP9_UPI="$UPI" GROUP9_PROJECT_ROOT="$PROJECT"
cd -- "$PROJECT"
bash generation/all_experiments/submit_all_slurm.sh --submit __SUBMIT_ARGS__
'@
    Invoke-RemoteBash ($Run.Replace('__VALUES__', $RemoteValues).Replace('__SUBMIT_ARGS__', $SubmitArgumentText)) 'Slurm submission'
    Write-Host 'SUBMISSION_RECORDS_READY: inspect the printed job_ids.tsv. Queue IDs are not completed GPU results.'
    Write-Host 'Use the guide to monitor/resume, then collect and download verified closed exports.'
}
finally { $OutputEncoding = $OriginalOutputEncoding }
