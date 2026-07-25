param([string]$LockFile = 'requirements/modern-x64.lock', [string]$Wheelhouse = 'wheelhouse')
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $LockFile)) { throw "Missing lock file: $LockFile" }
if (-not (Test-Path $Wheelhouse)) { throw "Missing wheelhouse: $Wheelhouse" }
python -m pip install --dry-run --no-index --find-links $Wheelhouse --require-hashes -r $LockFile

