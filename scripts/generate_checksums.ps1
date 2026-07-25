$ErrorActionPreference = 'Stop'
$files = Get-ChildItem dist -File -Recurse -Include *.exe,*.zip,*.dll -ErrorAction SilentlyContinue
if (-not $files) { throw 'No release artifacts found under dist' }
$lines = foreach ($f in $files) { $h = Get-FileHash $f.FullName -Algorithm SHA256; "$($h.Hash.ToLowerInvariant())  $($f.FullName.Replace((Get-Location).Path + '\',''))" }
$lines | Set-Content -Encoding UTF8 SHA256SUMS.txt

