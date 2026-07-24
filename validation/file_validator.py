from __future__ import annotations
from pathlib import Path
def validate_file_basic(path: Path) -> tuple[dict[str,bool], tuple[str,...], tuple[str,...]]:
    checks={"exists":path.exists(), "non_zero":path.exists() and path.stat().st_size>0, "extension_present":bool(path.suffix)}
    return checks, (), tuple(name for name, ok in checks.items() if not ok)
