from __future__ import annotations
import logging
from pathlib import Path
from storage.database import Database
def configure_logging(runtime_root: Path) -> None:
    log_dir=runtime_root/"logs"; log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s", handlers=[logging.FileHandler(log_dir/"excel_processor.log", encoding="utf-8"), logging.StreamHandler()])
def bootstrap(runtime_root: Path = Path("runtime")) -> Database:
    configure_logging(runtime_root); db=Database(runtime_root/"database"/"excel_processor.db"); db.migrate(); return db
