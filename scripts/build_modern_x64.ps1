$ErrorActionPreference = 'Stop'
$env:EXCEL_PROCESSOR_PAYLOAD_NAME = 'payload-modern-x64'
& '.build-env\modern-x64\Scripts\python.exe' -m pytest
& '.build-env\modern-x64\Scripts\pyinstaller.exe' --noconfirm build/excel_processor.spec --distpath dist

