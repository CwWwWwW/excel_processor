param([string]$Payload = 'dist/payload-modern-x64')
$ErrorActionPreference = 'Stop'
$exe = Join-Path $Payload 'ExcelProcessor.exe'
if (-not (Test-Path $exe)) { throw "Missing executable: $exe" }
& $exe --self-check
if ($LASTEXITCODE -ne 0) { throw "Payload self-check failed: $Payload" }

