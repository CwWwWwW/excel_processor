from __future__ import annotations
import hashlib, zipfile
from pathlib import Path
from typing import Iterable
from pydantic import BaseModel, ConfigDict, field_serializer
class DiscoveredFile(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"; path: Path; extension: str; size_bytes: int; sha256: str; has_vba: bool=False; is_locked: bool=False; warnings: tuple[str,...]=()
    @field_serializer("path")
    def _p(self, v: Path) -> str: return str(v)
def sha256_file(path: Path, chunk_size: int = 1024*1024) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""): h.update(chunk)
    return h.hexdigest()
def has_vba_project(path: Path) -> bool:
    ext=path.suffix.lower()
    if ext in {".xls", ".xlsb"}: return True
    if ext in {".xlsm", ".xltm", ".xlam"}:
        try:
            with zipfile.ZipFile(path) as zf: return any(n.endswith("vbaProject.bin") for n in zf.namelist())
        except Exception: return True
    return False
def is_locked(path: Path) -> bool:
    try:
        with path.open("ab"): return False
    except OSError: return True
def scan_files(paths: Iterable[Path], recursive: bool=False) -> tuple[DiscoveredFile,...]:
    out=[]
    for input_path in paths:
        candidates = input_path.rglob("*") if input_path.is_dir() and recursive else ([input_path] if input_path.is_file() else input_path.glob("*") if input_path.is_dir() else [])
        for path in candidates:
            if path.is_file(): out.append(DiscoveredFile(path=path, extension=path.suffix.lower(), size_bytes=path.stat().st_size, sha256=sha256_file(path), has_vba=has_vba_project(path), is_locked=is_locked(path)))
    return tuple(out)
