$ErrorActionPreference = 'Stop'
python -m pytest
python scripts/generate_operation_catalog.py
$catalog = Get-Content resources/operation_catalog.json -Raw
if ($catalog -match 'stand-in|sample|test-double|\?\?\?\?') { throw 'Catalog contains forbidden stand-in text' }
foreach ($p in 'dist/payload-modern-x64/ExcelProcessor.exe','dist/payload-modern-x64/excel_worker.exe','dist/payload-legacy-x64/ExcelProcessor.exe','dist/payload-legacy-x86/ExcelProcessor.exe') {
  if (-not (Test-Path $p)) { throw "Missing release payload file: $p" }
}
if (-not (Test-Path 'SHA256SUMS.txt')) { throw 'Missing SHA256SUMS.txt' }
if (-not (Test-Path 'SBOM.spdx.json')) { throw 'Missing SBOM.spdx.json' }
python scripts/verify_checksums.py
python scripts/verify_sbom.py

