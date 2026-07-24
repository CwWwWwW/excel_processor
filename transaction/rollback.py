from __future__ import annotations
import shutil
from pathlib import Path
from uuid import uuid4
def reject_candidate(candidate: Path, rejected_dir: Path) -> Path:
    rejected_dir.mkdir(parents=True, exist_ok=True); target=rejected_dir/f'{uuid4().hex}_{candidate.name}'
    if candidate.exists(): shutil.move(str(candidate), str(target))
    return target
