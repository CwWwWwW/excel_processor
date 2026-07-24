param([string]$Exe='dist/payload-modern-x64/ExcelProcessor.exe')
$ErrorActionPreference='Stop'
& $Exe --self-check
