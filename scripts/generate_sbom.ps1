$ErrorActionPreference='Stop'
$items = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch '\\.git\\|runtime\\|\\.pytest_cache\\' } | Select-Object FullName,Length
@{spdxVersion='SPDX-2.3'; name='ExcelProcessor-1.0.1'; files=$items} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 SBOM.spdx.json
