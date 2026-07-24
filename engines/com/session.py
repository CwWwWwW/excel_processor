from __future__ import annotations
from pathlib import Path
from typing import Any
XL_CALCULATION_MANUAL = -4135
MSO_AUTOMATION_SECURITY_FORCE_DISABLE = 3
class ExcelComSession:
    def __init__(self, visible: bool = False, allow_macros: bool = False) -> None:
        self.visible = visible; self.allow_macros = allow_macros; self.app: Any | None = None; self._previous: dict[str, Any] = {}; self._pythoncom = None; self.excel_pid: int | None = None; self.hwnd: int | None = None
    def __enter__(self):
        import pythoncom, win32com.client
        self._pythoncom = pythoncom; pythoncom.CoInitialize(); self.app = win32com.client.DispatchEx("Excel.Application")
        for name in ("DisplayAlerts", "ScreenUpdating", "EnableEvents", "Calculation", "AutomationSecurity", "AskToUpdateLinks"):
            try:
                self._previous[name] = getattr(self.app, name)
            except Exception as exc:
                _ = exc
        self.app.Visible = self.visible; self.app.DisplayAlerts = False; self.app.ScreenUpdating = False; self.app.EnableEvents = False; self.app.Calculation = XL_CALCULATION_MANUAL; self.app.AskToUpdateLinks = False
        if not self.allow_macros: self.app.AutomationSecurity = MSO_AUTOMATION_SECURITY_FORCE_DISABLE
        self.hwnd = int(getattr(self.app, "Hwnd", 0) or 0); self.excel_pid = self._pid_from_hwnd(self.hwnd)
        return self
    def _pid_from_hwnd(self, hwnd: int) -> int | None:
        if not hwnd: return None
        try:
            import win32process
            return int(win32process.GetWindowThreadProcessId(hwnd)[1])
        except Exception as exc:
            _ = exc
            return None
    def open_workbook(self, path: Path, read_only: bool = False) -> Any:
        if self.app is None: raise RuntimeError("Excel COM session is not started")
        return self.app.Workbooks.Open(str(path), UpdateLinks=0, ReadOnly=read_only, IgnoreReadOnlyRecommended=True, AddToMru=False)
    def __exit__(self, exc_type, exc, tb) -> None:
        if self.app is not None:
            for name, value in self._previous.items():
                try:
                    setattr(self.app, name, value)
                except Exception as restore_exc:
                    _ = restore_exc
            try:
                self.app.Quit()
            except Exception as quit_exc:
                _ = quit_exc
        if self._pythoncom is not None: self._pythoncom.CoUninitialize()
