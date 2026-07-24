from __future__ import annotations
from pathlib import Path
def list_recoverable_jobs(runtime_root: Path) -> tuple[Path,...]:
    jobs=runtime_root/"jobs"
    return tuple(p for p in jobs.iterdir() if p.is_dir()) if jobs.exists() else ()
