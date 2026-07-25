param([string]$LockFile = 'requirements/modern-x64.lock', [string]$Wheelhouse = 'wheelhouse')
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $Wheelhouse | Out-Null
python -m pip download --only-binary=:all: --require-hashes -r $LockFile -d $Wheelhouse

