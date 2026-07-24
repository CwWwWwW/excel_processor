from __future__ import annotations
import shutil
from pathlib import Path
def reject_candidate(candidate: Path, rejected_dir: Path) -> Path:
    rejected_dir.mkdir(parents=True, exist_ok=True); target=rejected_dir/candidate.name
    if candidate.exists(): shutil.move(str(candidate), str(target))
    return target
