from __future__ import annotations
import json, shutil
from pathlib import Path
from uuid import UUID, uuid4
from contracts.job import FileSpec
from discovery.file_scanner import sha256_file
class JobWorkspace:
    def __init__(self, runtime_root: Path, job_id: UUID) -> None:
        self.job_id=job_id; self.root=runtime_root/'jobs'/str(job_id); self.backup=self.root/'backup'; self.working=self.root/'working'; self.candidate=self.root/'candidate'; self.committed=self.root/'committed'; self.rejected=self.root/'rejected'; self.reports=self.root/'reports'; self.logs=self.root/'logs'; self.temp=self.root/'temp'
    def ensure(self) -> None:
        for p in (self.backup,self.working,self.candidate,self.committed,self.rejected,self.reports,self.logs,self.temp): p.mkdir(parents=True, exist_ok=True)
    def _safe_name(self, source: Path) -> str:
        return source.name[:120]
    def prepare_file(self, file_spec: FileSpec) -> Path:
        self.ensure(); source=file_spec.source_path.resolve(); source_hash=sha256_file(source); manifest=self.backup/f'{file_spec.file_id}.manifest.json'; backup_path=self.backup/f'{file_spec.file_id}_{source_hash[:12]}_{self._safe_name(source)}'; working_path=self.working/f'{file_spec.file_id}_{uuid4().hex}_{self._safe_name(source)}'
        if backup_path.exists():
            existing=json.loads(manifest.read_text(encoding='utf-8')) if manifest.exists() else {}
            if existing.get('source_sha256') != source_hash: raise ValueError('Existing source backup hash does not match current source file')
        else:
            shutil.copy2(source, backup_path); manifest.write_text(json.dumps({'source_path':str(source),'source_sha256':source_hash,'backup_path':str(backup_path)}, ensure_ascii=False, indent=2), encoding='utf-8')
        shutil.copy2(source, working_path); return working_path
    def candidate_path_for(self, source: Path) -> Path:
        self.ensure(); return self.candidate/f'{uuid4().hex}_{source.name[:120]}'
    def committed_path_for(self, source: Path) -> Path:
        self.ensure(); return self.committed/f'{uuid4().hex}_{source.name[:120]}'
    def cleanup_temp(self) -> None:
        self.temp.mkdir(parents=True, exist_ok=True)
        for item in self.temp.iterdir():
            if item.is_file():
                try: item.unlink()
                except OSError as exc:
                    _ = exc
