from __future__ import annotations
import fnmatch
from contracts.job import FileSpec
from contracts.operation import TargetSpec
def resolve_files(target: TargetSpec, files: tuple[FileSpec,...]) -> tuple[FileSpec,...]:
    selected=files
    if target.file_ids is not None:
        ids=set(target.file_ids); selected=tuple(f for f in selected if f.file_id in ids)
    if target.file_name_pattern:
        selected=tuple(f for f in selected if fnmatch.fnmatch(f.source_path.name, target.file_name_pattern))
    return selected
