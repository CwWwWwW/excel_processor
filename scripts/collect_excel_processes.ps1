$ErrorActionPreference = 'Stop'
Get-Process EXCEL -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,Path,StartTime | ConvertTo-Json -Depth 3

