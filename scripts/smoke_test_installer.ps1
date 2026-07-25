param([string]$Installer)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Installer)) { throw "Missing installer: $Installer" }
$log = Join-Path $env:TEMP 'excel_processor_install.log'
Start-Process -FilePath $Installer -ArgumentList "/VERYSILENT /NORESTART /LOG=`"$log`"" -Wait
if ($LASTEXITCODE -ne 0) { throw "Installer returned non-zero exit code" }

