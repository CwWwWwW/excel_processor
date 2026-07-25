param([string]$Version = '1.0.1')
$ErrorActionPreference = 'Stop'
$payloads = @(
  @{Dir='payload-modern-x64'; Zip="ExcelProcessor-$Version-Portable-x64.zip"},
  @{Dir='payload-legacy-x64'; Zip="ExcelProcessor-$Version-Portable-Legacy-x64.zip"},
  @{Dir='payload-legacy-x86'; Zip="ExcelProcessor-$Version-Portable-Legacy-x86.zip"}
)
foreach ($p in $payloads) {
  $dir = Join-Path 'dist' $p.Dir
  if (-not (Test-Path $dir)) { throw "Missing payload: $dir" }
  New-Item -ItemType File -Force -Path (Join-Path $dir 'portable.flag') | Out-Null
  Compress-Archive -Path (Join-Path $dir '*') -DestinationPath (Join-Path 'dist' $p.Zip) -Force
}

