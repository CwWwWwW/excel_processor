$ErrorActionPreference='Stop'
Write-Host 'Run on Python 3.8 x86 build VM with requirements/legacy-x86.lock'
pyinstaller --noconfirm build/excel_processor.spec --distpath dist/payload-legacy-x86-build
