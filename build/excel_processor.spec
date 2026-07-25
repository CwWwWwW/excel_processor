# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

PAYLOAD_NAME = os.environ.get("EXCEL_PROCESSOR_PAYLOAD_NAME", "payload-modern-x64")
block_cipher = None
_datas = [("resources", "resources"), ("storage/migrations", "storage/migrations"), ("excel_processor", "excel_processor")]
_binaries = []
_hidden = ["ui.qt_compat", "workers.excel_worker_common", "workers.excel_worker_x64.main", "workers.excel_worker_x86.main"]
_required_packages = ("pandas", "numpy", "openpyxl", "win32com", "pythoncom", "pywintypes")
_missing = []
for pkg in _required_packages:
    try:
        d, b, h = collect_all(pkg)
        _datas += d
        _binaries += b
        _hidden += h
    except Exception as exc:
        _missing.append(f"{pkg}: {exc}")
if _missing:
    raise RuntimeError("PyInstaller dependency collection failed: " + "; ".join(_missing))

a = Analysis(["app/main.py"], pathex=[], binaries=_binaries, datas=_datas, hiddenimports=_hidden, hookspath=[], hooksconfig={}, runtime_hooks=["build/pywin32_runtime_hook.py", "build/local_data_path_hook.py"], excludes=[], noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="ExcelProcessor", debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False, manifest="build/windows_app.manifest", version="build/version_info.txt")
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name=PAYLOAD_NAME)
