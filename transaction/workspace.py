from __future__ import annotations
import shutil
from pathlib import Path
from uuid import UUID
from contracts.job import FileSpec
class JobWorkspace:
    def __init__(self, runtime_root: Path, job_id: UUID) -> None:
        self.root=runtime_root/"jobs"/str(job_id); self.backup=self.root/"backup"; self.working=self.root/"working"; self.candidate=self.root/"candidate"; self.committed=self.root/"committed"; self.rejected=self.root/"rejected"; self.reports=self.root/"reports"; self.logs=self.root/"logs"
    def ensure(self) -> None:
        for p in (self.backup,self.working,self.candidate,self.committed,self.rejected,self.reports,self.logs): p.mkdir(parents=True, exist_ok=True)
    def prepare_file(self, file_spec: FileSpec) -> Path:
        self.ensure(); source=file_spec.source_path; backup_path=self.backup/f"{file_spec.file_id}_{source.name}"; working_path=self.working/f"{file_spec.file_id}_{source.name}"
        if not backup_path.exists(): shutil.copy2(source, backup_path)
        shutil.copy2(source, working_path); return working_path
