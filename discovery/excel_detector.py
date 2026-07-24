from __future__ import annotations
import platform as _platform
from pathlib import Path
from typing import Any
from contracts.capability import CapabilityProfile, ExcelInstallation
from .registry_reader import C2R_PATH, read_registry_value
from .typelib_scanner import enumerate_file_formats, scan_typelib_members
def get_file_version(executable: Path) -> str | None:
    try:
        import win32api
        info = win32api.GetFileVersionInfo(str(executable), "\\"); ms=info["FileVersionMS"]; ls=info["FileVersionLS"]
        return ".".join(map(str,(win32api.HIWORD(ms),win32api.LOWORD(ms),win32api.HIWORD(ls),win32api.LOWORD(ls))))
    except Exception: return None
def classify_excel(com_version: str, product_ids: str | None) -> str:
    if com_version.startswith("12."): return "Microsoft Excel 2007"
    if com_version.startswith("14."): return "Microsoft Excel 2010"
    if com_version.startswith("15."): return "Microsoft Excel 2013"
    if not com_version.startswith("16."): return f"未知 Excel 系列 ({com_version})"
    ids=(product_ids or "").lower()
    if "2024" in ids: return "Microsoft Excel 2024 / LTSC 2024"
    if "2021" in ids: return "Microsoft Excel 2021 / LTSC 2021"
    if "2019" in ids: return "Microsoft Excel 2019"
    if "2016" in ids: return "Microsoft Excel 2016"
    if "o365" in ids or "microsoft365" in ids: return "Microsoft 365 Excel"
    return "Microsoft Excel 16.0 系列"
def _detect_bitness(executable: Path | None, registry_platform: str | None) -> str | None:
    if registry_platform:
        low=registry_platform.lower()
        if "x64" in low or "64" in low: return "64-bit"
        if "x86" in low or "32" in low: return "32-bit"
    return None
def detect_excel() -> ExcelInstallation:
    if _platform.system() != "Windows": return ExcelInstallation(installed=False, error="Excel COM detection requires Windows")
    try:
        import pythoncom, win32com.client
    except Exception as exc: return ExcelInstallation(installed=False, error=str(exc))
    app: Any | None = None; pythoncom.CoInitialize()
    try:
        app = win32com.client.gencache.EnsureDispatch("Excel.Application")
        executable = Path(str(app.Path)) / "EXCEL.EXE"; com_version = str(app.Version)
        product_ids = read_registry_value(C2R_PATH, "ProductReleaseIds"); platform = read_registry_value(C2R_PATH, "Platform")
        return ExcelInstallation(installed=True, display_name=classify_excel(com_version, product_ids), com_version=com_version, build=str(app.Build), file_version=get_file_version(executable), executable=executable, operating_system=str(app.OperatingSystem), product_release_ids=product_ids, version_to_report=read_registry_value(C2R_PATH,"VersionToReport"), platform=platform, update_channel=read_registry_value(C2R_PATH,"UpdateChannel"), bitness=_detect_bitness(executable, platform))
    except Exception as exc: return ExcelInstallation(installed=False, error=str(exc))
    finally:
        if app is not None:
            try: app.Quit()
            except Exception: pass
        pythoncom.CoUninitialize()
def build_capability_profile() -> CapabilityProfile:
    excel = detect_excel(); members = scan_typelib_members() if excel.installed else {}
    return CapabilityProfile(excel=excel, supported_file_formats=enumerate_file_formats(), typelib_members=members, power_query_available="WorkbookQuery" in " ".join(members.get("Application", ())), data_model_available=excel.installed and (excel.com_version or "").startswith("16."), raw={"source":"live-com" if excel.installed else "fallback"})
