from __future__ import annotations
from contracts.capability import CapabilityProfile
def choose_excel_worker(capability: CapabilityProfile) -> str:
    bitness=(capability.excel.bitness or capability.excel.platform or "").lower()
    if "32" in bitness or "x86" in bitness: return "excel_worker_x86.exe"
    return "excel_worker_x64.exe"
