from __future__ import annotations
from pathlib import Path
from typing import Any
XL_CALCULATION_MANUAL=-4135; MSO_AUTOMATION_SECURITY_FORCE_DISABLE=3
class ExcelComSession:
    def __init__(self, visible: bool=False, allow_macros: bool=False) -> None:
        self.visible=visible; self.allow_macros=allow_macros; self.app: Any|None=None; self._previous={}; self._pythoncom=None
    def __enter__(self):
        import pythoncom, win32com.client
        self._pythoncom=pythoncom; pythoncom.CoInitialize(); self.app=win32com.client.DispatchEx("Excel.Application")
        for name in ("DisplayAlerts","ScreenUpdating","EnableEvents","Calculation","AutomationSecurity"):
            try: self._previous[name]=getattr(self.app,name)
            except Exception: pass
        self.app.Visible=self.visible; self.app.DisplayAlerts=False; self.app.ScreenUpdating=False; self.app.EnableEvents=False; self.app.Calculation=XL_CALCULATION_MANUAL
        if not self.allow_macros: self.app.AutomationSecurity=MSO_AUTOMATION_SECURITY_FORCE_DISABLE
        return self
    def open_workbook(self, path: Path, read_only: bool=False) -> Any:
        if self.app is None: raise RuntimeError("Excel COM 会话尚未启动")
        return self.app.Workbooks.Open(str(path), UpdateLinks=0, ReadOnly=read_only, IgnoreReadOnlyRecommended=True, AddToMru=False)
    def __exit__(self, exc_type, exc, tb) -> None:
        if self.app is not None:
            for name,value in self._previous.items():
                try: setattr(self.app,name,value)
                except Exception: pass
            try: self.app.Quit()
            except Exception: pass
        if self._pythoncom is not None: self._pythoncom.CoUninitialize()
