$ErrorActionPreference='Stop'
Get-ChildItem dist -File -Recurse -Include *.exe,*.zip -ErrorAction SilentlyContinue | ForEach-Object { $h=Get-FileHash $_.FullName -Algorithm SHA256; "$($h.Hash)  $($_.Name)" } | Set-Content -Encoding UTF8 SHA256SUMS.txt
