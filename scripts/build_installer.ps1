$ErrorActionPreference = 'Stop'
foreach ($p in 'payload-modern-x64','payload-legacy-x64','payload-legacy-x86') {
  if (-not (Test-Path (Join-Path 'dist' $p))) { throw "Missing payload: dist/$p" }
}
$ISCC = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
if (-not (Test-Path $ISCC)) { throw "Inno Setup 6 is not installed at $ISCC" }
& $ISCC installer/ExcelProcessor.iss

