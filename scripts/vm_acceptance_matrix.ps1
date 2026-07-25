$ErrorActionPreference='Stop'
& (Join-Path $PSScriptRoot 'run_excel_compatibility_suite.ps1') -Output 'compatibility-results/local-vm.json'
