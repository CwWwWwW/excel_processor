from __future__ import annotations
import argparse
from pathlib import Path
from app.bootstrap import bootstrap
from discovery.excel_detector import build_capability_profile
from scheduler.worker_manager import choose_excel_worker
def self_check() -> int:
    db=bootstrap(Path("runtime")); cap=build_capability_profile(); print("database=ok", db.path); print("excel_installed=", cap.excel.installed); print("excel_display=", cap.excel.display_name); print("worker=", choose_excel_worker(cap)); return 0
def main() -> int:
    parser=argparse.ArgumentParser(prog="excel-processor"); parser.add_argument("--self-check", action="store_true"); args=parser.parse_args()
    if args.self_check: return self_check()
    try:
        from ui.main_window import run_app
        return run_app()
    except Exception as exc:
        print(f"无法启动图形界面：{exc}"); return 2
if __name__ == "__main__": raise SystemExit(main())
