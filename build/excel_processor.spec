# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
block_cipher = None
_datas=[('resources','resources'),('storage/migrations','storage/migrations'),('excel_processor','excel_processor')]
_binaries=[]
_hidden=[]
for pkg in ('pandas','numpy','openpyxl','win32com','pythoncom','pywintypes'):
    try:
        d,b,h=collect_all(pkg); _datas+=d; _binaries+=b; _hidden+=h
    except Exception:
        pass
a = Analysis(['app/main.py'], pathex=[], binaries=_binaries, datas=_datas, hiddenimports=_hidden+['ui.qt_compat','workers.excel_worker_common'], hookspath=[], hooksconfig={}, runtime_hooks=[], excludes=[], noarchive=False)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ExcelProcessor', debug=False, bootloader_ignore_signals=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name='payload-modern-x64')
