param([string]$LockFile='requirements/modern-x64.lock')
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path wheelhouse | Out-Null
python -m pip download --only-binary=:all: --require-hashes -r $LockFile -d wheelhouse
