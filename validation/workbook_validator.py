from __future__ import annotations
from pathlib import Path
def validate_openxml_reopen(path: Path) -> tuple[bool, str | None]:
    if path.suffix.lower() not in {".xlsx",".xlsm",".xltx",".xltm"}: return True, "该格式跳过 OpenXML 重开验证，需 Excel COM 验证"
    try:
        from openpyxl import load_workbook
        wb=load_workbook(path, read_only=True, keep_vba=True); wb.close(); return True, None
    except Exception as exc: return False, str(exc)
