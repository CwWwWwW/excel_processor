from __future__ import annotations
import argparse
from app.bootstrap import bootstrap, write_crash_report
from discovery.excel_detector import build_capability_profile
from excel_processor.paths import ensure_runtime_root
from excel_processor.version import __version__
from scheduler.worker_manager import choose_excel_worker
def self_check() -> int:
    root=ensure_runtime_root(); db=bootstrap(root); cap=build_capability_profile(); print('version=', __version__); print('runtime=', root); print('database=ok', db.path); print('excel_installed=', cap.excel.installed); print('excel_display=', cap.excel.display_name); print('worker=', choose_excel_worker(cap)); return 0
def main() -> int:
    parser=argparse.ArgumentParser(prog='excel-processor'); parser.add_argument('--self-check', action='store_true'); args=parser.parse_args()
    if args.self_check: return self_check()
    try:
        from ui.main_window import run_app
        return run_app()
    except Exception as exc:
        root=ensure_runtime_root(); report=write_crash_report(exc, root); print(f'?????????{exc}; crash_report={report}'); return 2
if __name__ == '__main__': raise SystemExit(main())
