$ErrorActionPreference = 'Stop'
$env:EXCEL_PROCESSOR_PAYLOAD_NAME = 'payload-legacy-x64'
& '.build-env\legacy-x64\Scripts\python.exe' -m pytest
& '.build-env\legacy-x64\Scripts\pyinstaller.exe' --noconfirm build/excel_processor.spec --distpath dist

