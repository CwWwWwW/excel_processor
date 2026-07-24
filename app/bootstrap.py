from __future__ import annotations
import logging, sys, traceback
from pathlib import Path
from excel_processor.paths import ensure_runtime_root
from storage.database import Database, migrate_v1_0_0_runtime

def configure_logging(runtime_root: Path) -> None:
    log_dir=runtime_root/'logs'; log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s %(message)s', handlers=[logging.FileHandler(log_dir/'excel_processor.log', encoding='utf-8'), logging.StreamHandler()])
def write_crash_report(exc: BaseException, runtime_root: Path) -> Path:
    report_dir=runtime_root/'crash_reports'; report_dir.mkdir(parents=True, exist_ok=True); path=report_dir/'last_crash.txt'; path.write_text(''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)), encoding='utf-8'); return path
def bootstrap(runtime_root: Path | None=None) -> Database:
    root=runtime_root or ensure_runtime_root(); configure_logging(root); db=Database(root/'database'/'excel_processor.db'); db.migrate(); migrate_v1_0_0_runtime(Path.cwd()/'runtime', db); return db
