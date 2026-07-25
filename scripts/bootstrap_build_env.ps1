param([string]$Runtime='modern-x64')
$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'create_build_envs.ps1')
