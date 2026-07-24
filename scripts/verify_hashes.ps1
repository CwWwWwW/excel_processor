$ErrorActionPreference='Stop'
Get-ChildItem wheelhouse -File -ErrorAction SilentlyContinue | ForEach-Object { Get-FileHash $_.FullName -Algorithm SHA256 } | Format-Table
