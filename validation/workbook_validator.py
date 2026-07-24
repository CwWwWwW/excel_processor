from __future__ import annotations
import zipfile
from pathlib import Path
OOXML_EXTS={'.xlsx','.xlsm','.xltx','.xltm','.xlam'}
COM_REQUIRED_EXTS={'.xls','.xlsb','.xlt','.xla','.xlam','.xltm'}
def validate_ooxml_container(path: Path) -> tuple[bool, str | None]:
    if path.suffix.lower() not in OOXML_EXTS: return True, None
    try:
        with zipfile.ZipFile(path) as zf:
            names=set(zf.namelist())
            required={'[Content_Types].xml','_rels/.rels'}
            missing=required-names
            if missing: return False, f'OOXML ???????{sorted(missing)}'
            bad=zf.testzip()
            if bad: return False, f'OOXML ZIP ???{bad}'
        return True, None
    except Exception as exc: return False, str(exc)
def validate_openxml_reopen(path: Path) -> tuple[bool, str | None]:
    if path.suffix.lower() not in {'.xlsx','.xlsm','.xltx','.xltm'}: return True, None
    try:
        from openpyxl import load_workbook
        wb=load_workbook(path, read_only=True, keep_vba=path.suffix.lower() in {'.xlsm','.xltm'}); wb.close(); return True, None
    except Exception as exc: return False, str(exc)
def validate_excel_com_reopen(path: Path, excel_installed: bool) -> tuple[bool, str | None]:
    if path.suffix.lower() not in COM_REQUIRED_EXTS: return True, None
    if not excel_installed: return False, f'{path.suffix} ?? Excel COM ??????????? Excel'
    try:
        from engines.com.session import ExcelComSession
        workbook=None
        with ExcelComSession(visible=False, allow_macros=False) as session:
            workbook=session.open_workbook(path, read_only=True)
            workbook.Close(SaveChanges=False); workbook=None
        return True, None
    except Exception as exc:
        try:
            if workbook is not None: workbook.Close(SaveChanges=False)
        except Exception as close_exc:
            _ = close_exc
        return False, str(exc)
