$ErrorActionPreference='Stop'
Write-Host 'Run on Python 3.8 x64 build VM with requirements/legacy-x64.lock'
pyinstaller --noconfirm build/excel_processor.spec --distpath dist/payload-legacy-x64-build
