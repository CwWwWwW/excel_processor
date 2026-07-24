from __future__ import annotations
import os, shutil, time
from pathlib import Path
from uuid import uuid4
from discovery.file_scanner import sha256_file
class CommitError(RuntimeError):
    """Raised when a candidate file cannot be safely committed."""
def _unique_target(path: Path) -> Path:
    if not path.exists(): return path
    stem, suffix = path.stem, path.suffix; parent=path.parent
    for idx in range(1,10000):
        candidate=parent/f'{stem}_{idx}{suffix}'
        if not candidate.exists(): return candidate
    raise CommitError('???????????')
def _same_drive(a: Path, b: Path) -> bool:
    return a.resolve().drive.lower() == b.resolve().drive.lower()
def atomic_commit(candidate: Path, final_path: Path, overwrite_policy: str='rename', backup_dir: Path | None=None, retries: int=5, delay: float=0.2) -> Path:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    if not candidate.exists(): raise CommitError('?????????')
    if candidate.stat().st_size == 0: raise CommitError('????????')
    source_hash=sha256_file(candidate)
    target=final_path
    if target.exists():
        if overwrite_policy == 'reject': raise CommitError(f'??????{target}')
        if overwrite_policy == 'rename': target=_unique_target(target)
        elif overwrite_policy == 'replace_after_backup':
            bdir=backup_dir or target.parent/'output_backup'; bdir.mkdir(parents=True, exist_ok=True); shutil.copy2(target, bdir/f'{uuid4().hex}_{target.name}')
        else: raise CommitError(f'???????{overwrite_policy}')
    temp = target.with_name(f'.{target.name}.{uuid4().hex}.tmp')
    try:
        if _same_drive(candidate, target):
            shutil.copy2(candidate, temp)
        else:
            shutil.copy2(candidate, temp)
        if sha256_file(temp) != source_hash: raise CommitError('??? SHA-256 ????')
        last_error=None
        for _ in range(retries):
            try:
                os.replace(temp, target); break
            except OSError as exc:
                last_error=exc; time.sleep(delay); delay*=2
        else: raise CommitError(f'???????{last_error}')
        if sha256_file(target) != source_hash: raise CommitError('??? SHA-256 ????')
        return target
    finally:
        if temp.exists():
            try: temp.unlink()
            except OSError as exc:
                _ = exc
