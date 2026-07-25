param([string]$Exe='dist/payload-modern-x64/ExcelProcessor.exe')
$ErrorActionPreference='Stop'
& $Exe --self-check
if ($LASTEXITCODE -ne 0) { throw 'Self-check failed' }
