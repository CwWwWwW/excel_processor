from __future__ import annotations
import platform as _platform
from pathlib import Path
from typing import Any
from contracts.capability import CapabilityProfile, ExcelInstallation
from .platform_detector import detect_platform
from .registry_reader import C2R_PATH, read_registry_value
from .typelib_scanner import enumerate_file_formats, scan_typelib_members

def get_file_version(executable: Path) -> str | None:
    try:
        import win32api
        info = win32api.GetFileVersionInfo(str(executable), "\\")
        ms = info["FileVersionMS"]; ls = info["FileVersionLS"]
        return ".".join(map(str, (win32api.HIWORD(ms), win32api.LOWORD(ms), win32api.HIWORD(ls), win32api.LOWORD(ls))))
    except Exception as exc:
        _ = exc
        return None

def classify_excel(com_version: str, product_ids: str | None, msi_name: str | None = None) -> tuple[str, str]:
    if com_version.startswith("12."): return "Microsoft Excel 2007", "C"
    if com_version.startswith("14."): return "Microsoft Excel 2010", "B"
    if com_version.startswith("15."): return "Microsoft Excel 2013", "B"
    if not com_version.startswith("16."): return f"Unknown Excel series ({com_version})", "unknown"
    ids = ((product_ids or "") + " " + (msi_name or "")).lower()
    if "2024" in ids: return "Microsoft Excel 2024 / LTSC 2024", "A"
    if "2021" in ids: return "Microsoft Excel 2021 / LTSC 2021", "A"
    if "2019" in ids: return "Microsoft Excel 2019", "A"
    if "2016" in ids: return "Microsoft Excel 2016", "A"
    if "o365" in ids or "microsoft365" in ids or "365" in ids: return "Microsoft 365 Excel", "A"
    return "Microsoft Excel 16.0 series", "A"

def _detect_bitness(executable: Path | None, registry_platform: str | None) -> str | None:
    if registry_platform:
        low = registry_platform.lower()
        if "x64" in low or "64" in low: return "64-bit"
        if "x86" in low or "32" in low: return "32-bit"
    if executable and executable.exists():
        try:
            import struct
            with executable.open("rb") as f:
                f.seek(0x3C); offset = struct.unpack("<I", f.read(4))[0]
                f.seek(offset + 4); machine = struct.unpack("<H", f.read(2))[0]
            return "64-bit" if machine == 0x8664 else "32-bit" if machine == 0x14C else None
        except Exception as exc:
            _ = exc
    return None

def _read_msi_name() -> str | None:
    for path in (r"SOFTWARE\Microsoft\Office\16.0\Excel\InstallRoot", r"SOFTWARE\Microsoft\Office\15.0\Excel\InstallRoot", r"SOFTWARE\Microsoft\Office\14.0\Excel\InstallRoot", r"SOFTWARE\Microsoft\Office\12.0\Excel\InstallRoot"):
        value = read_registry_value(path, "Path")
        if value: return path
    return None

def _read_app_paths() -> Path | None:
    value = read_registry_value(r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe", "")
    return Path(value) if value else None

def detect_excel() -> ExcelInstallation:
    if _platform.system() != "Windows": return ExcelInstallation(installed=False, error="Excel COM detection requires Windows")
    try:
        import pythoncom, win32com.client
    except Exception as exc:
        return ExcelInstallation(installed=False, error=str(exc))
    app: Any | None = None
    pythoncom.CoInitialize()
    try:
        app = win32com.client.gencache.EnsureDispatch("Excel.Application")
        executable = Path(str(app.Path)) / "EXCEL.EXE"; com_version = str(app.Version)
        product_ids = read_registry_value(C2R_PATH, "ProductReleaseIds"); office_platform = read_registry_value(C2R_PATH, "Platform"); msi_name = _read_msi_name()
        display, level = classify_excel(com_version, product_ids, msi_name)
        return ExcelInstallation(installed=True, display_name=display, support_level=level, com_version=com_version, build=str(app.Build), file_version=get_file_version(executable), executable=executable, operating_system=str(app.OperatingSystem), product_release_ids=product_ids, version_to_report=read_registry_value(C2R_PATH, "VersionToReport"), platform=office_platform, update_channel=read_registry_value(C2R_PATH, "UpdateChannel"), msi_product_name=msi_name, app_paths_executable=_read_app_paths(), bitness=_detect_bitness(executable, office_platform), hwnd=int(getattr(app, "Hwnd", 0) or 0))
    except Exception as exc:
        return ExcelInstallation(installed=False, error=str(exc))
    finally:
        if app is not None:
            try:
                app.Quit()
            except Exception as exc:
                _ = exc
        pythoncom.CoUninitialize()

def build_capability_profile() -> CapabilityProfile:
    excel = detect_excel(); members = scan_typelib_members() if excel.installed else {}; runtime_members = frozenset(members.get("Application", ()))
    platform_profile = detect_platform(excel)
    return CapabilityProfile(excel=excel, platform=platform_profile, supported_file_formats=enumerate_file_formats(), typelib_members=members, runtime_members=runtime_members, power_query_available="Queries" in runtime_members or "WorkbookQuery" in " ".join(members.get("Application", ())), data_model_available=excel.installed and (excel.com_version or "").startswith("16."), raw={"source": "live-com" if excel.installed else "fallback"})
