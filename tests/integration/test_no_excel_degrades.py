from discovery.excel_detector import build_capability_profile
from scheduler.worker_manager import choose_excel_worker

def test_capability_profile_is_always_available():
    profile = build_capability_profile()
    assert profile.schema_version == '1.0'
    assert choose_excel_worker(profile) in {'excel_worker_x86.exe', 'excel_worker_x64.exe'}
