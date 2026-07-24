from __future__ import annotations
import shutil
from pathlib import Path
def create_backup(source: Path, backup_path: Path) -> Path:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    if not backup_path.exists(): shutil.copy2(source, backup_path)
    return backup_path
