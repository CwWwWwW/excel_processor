param([string]$Runtime='modern-x64')
$ErrorActionPreference='Stop'
New-Item -ItemType Directory -Force -Path build_logs,wheelhouse,dist | Out-Null
Write-Host "Bootstrap clean build environment for $Runtime"
