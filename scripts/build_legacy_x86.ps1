$ErrorActionPreference = 'Stop'
$env:EXCEL_PROCESSOR_PAYLOAD_NAME = 'payload-legacy-x86'
& '.build-env\legacy-x86\Scripts\python.exe' -m pytest
& '.build-env\legacy-x86\Scripts\pyinstaller.exe' --noconfirm build/excel_processor.spec --distpath dist

