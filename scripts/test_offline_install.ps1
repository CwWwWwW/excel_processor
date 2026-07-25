param([string]$Runtime = 'modern-x64', [string]$Wheelhouse = 'wheelhouse')
$ErrorActionPreference = 'Stop'
$py = ".build-env\$Runtime\Scripts\python.exe"
if (-not (Test-Path $py)) { throw "Missing build environment: $Runtime" }
& $py -m pip install --no-index --find-links $Wheelhouse --require-hashes -r "requirements\$Runtime.lock"
& $py -m pip install --no-index --find-links $Wheelhouse .

