from __future__ import annotations
import platform
C2R_PATH = r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration"
def read_registry_value(path: str, name: str) -> str | None:
    if platform.system() != "Windows": return None
    try: import winreg
    except Exception: return None
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, path, 0, winreg.KEY_READ | view) as key:
                    value, _ = winreg.QueryValueEx(key, name); return str(value)
            except OSError: continue
    return None
