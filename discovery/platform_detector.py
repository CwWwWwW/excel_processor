from __future__ import annotations
import platform
from contracts.capability import ExcelInstallation, PlatformProfile

def _build_number(release: str, version: str) -> int:
    try:
        return int((version.split('.') + ['0','0','0'])[2])
    except Exception:
        return 0

def choose_runtime_family(windows_version: str, build: int, arch: str, service_pack: str | None) -> str:
    arch_l = arch.lower()
    if '32' in arch_l or 'x86' in arch_l and '64' not in arch_l:
        return 'legacy-x86'
    if windows_version.startswith('6.1') or windows_version.startswith('6.2') or windows_version.startswith('6.3'):
        return 'legacy-x64'
    if windows_version.startswith('10.') and build < 17763:
        return 'legacy-x64'
    return 'modern-x64'

def detect_platform(excel: ExcelInstallation | None = None) -> PlatformProfile:
    uname = platform.uname()
    version = platform.version()
    build = _build_number(platform.release(), version)
    sp = platform.win32_ver()[2] if hasattr(platform, 'win32_ver') else None
    arch = platform.machine() or platform.architecture()[0]
    runtime = choose_runtime_family(version, build, arch, sp)
    caps = {'windows', runtime, arch.lower()}
    if version.startswith('6.1') and sp and 'Service Pack 1' not in sp:
        caps.add('blocked-win7-without-sp1')
    return PlatformProfile(windows_name=f"{uname.system} {uname.release}".strip(), windows_version=version, windows_build=build, service_pack=sp or None, architecture=arch, runtime_family=runtime, excel=excel or ExcelInstallation(), capabilities=frozenset(caps))
