from __future__ import annotations
from contracts.capability import FileFormatCapability
FALLBACK_FORMATS = (
    FileFormatCapability(menu_name="保持源格式", extension="", file_format=None, category="workbook", can_preserve_vba=True),
    FileFormatCapability(menu_name="Excel 工作簿", extension=".xlsx", file_format=51, category="workbook"),
    FileFormatCapability(menu_name="启用宏的工作簿", extension=".xlsm", file_format=52, category="workbook", can_preserve_vba=True),
    FileFormatCapability(menu_name="Excel 二进制工作簿", extension=".xlsb", file_format=50, category="workbook", can_preserve_vba=True),
    FileFormatCapability(menu_name="严格 Open XML 工作簿", extension=".xlsx", file_format=61, category="workbook"),
    FileFormatCapability(menu_name="Excel 97-2003 工作簿", extension=".xls", file_format=56, category="workbook", can_preserve_vba=True),
    FileFormatCapability(menu_name="Excel 模板", extension=".xltx", file_format=54, category="template"),
    FileFormatCapability(menu_name="启用宏的模板", extension=".xltm", file_format=53, category="template", can_preserve_vba=True),
    FileFormatCapability(menu_name="Excel 加载项", extension=".xlam", file_format=55, category="addin", can_preserve_vba=True),
    FileFormatCapability(menu_name="CSV", extension=".csv", file_format=6, category="data", may_lose_objects=True),
    FileFormatCapability(menu_name="CSV UTF-8", extension=".csv", file_format=62, category="data", may_lose_objects=True),
    FileFormatCapability(menu_name="Unicode 文本", extension=".txt", file_format=42, category="data", may_lose_objects=True),
    FileFormatCapability(menu_name="PDF", extension=".pdf", file_format=57, category="fixed", may_lose_objects=True),
    FileFormatCapability(menu_name="XPS", extension=".xps", file_format=58, category="fixed", may_lose_objects=True),
)
def scan_typelib_members() -> dict[str, tuple[str, ...]]:
    try:
        import win32com.client
        app = win32com.client.Dispatch("Excel.Application")
        out = {"Application": tuple(sorted(n for n in dir(app) if not n.startswith("_"))), "Workbooks": tuple(sorted(n for n in dir(app.Workbooks) if not n.startswith("_")))}
        app.Quit(); return out
    except Exception: return {}
def enumerate_file_formats() -> tuple[FileFormatCapability, ...]: return FALLBACK_FORMATS
