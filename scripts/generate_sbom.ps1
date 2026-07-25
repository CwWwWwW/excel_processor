$ErrorActionPreference = 'Stop'
$packages = python -m pip list --format=json | ConvertFrom-Json
$files = Get-ChildItem dist -File -Recurse -ErrorAction SilentlyContinue | ForEach-Object { @{path=$_.FullName.Replace((Get-Location).Path + '\',''); sha256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(); size=$_.Length} }
if (-not $files) { throw 'No dist files available for SBOM' }
@{spdxVersion='SPDX-2.3'; name='ExcelProcessor-1.0.1'; packages=$packages; files=$files; generatedAt=(Get-Date).ToUniversalTime().ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 SBOM.spdx.json

