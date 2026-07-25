param([string]$Runtime = 'modern-x64')
$ErrorActionPreference = 'Stop'
$venv = ".build-env\$Runtime\Scripts\python.exe"
if (-not (Test-Path $venv)) { throw "Missing build environment: $Runtime" }
& $venv -m pip install pip-tools==7.4.1
$constraint = "requirements\$Runtime.in"
if (-not (Test-Path $constraint)) { throw "Missing requirement input: $constraint" }
& $venv -m piptools compile --generate-hashes --resolver=backtracking --output-file "requirements\$Runtime.lock" $constraint

