from __future__ import annotations
import hashlib
from pathlib import Path
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_serializer
class WorkbookSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"; file_id: UUID; source_path: Path; sha256: str; sheets: tuple[str,...]=(); has_vba: bool=False; object_counts: dict[str,int]=Field(default_factory=dict); warnings: tuple[str,...]=()
    @field_serializer("source_path")
    def _p(self, v: Path) -> str: return str(v)
    def stable_hash(self) -> str: return hashlib.sha256(self.model_dump_json().encode("utf-8")).hexdigest()
def inspect_workbook(file_id: UUID, path: Path) -> WorkbookSnapshot:
    from .file_scanner import has_vba_project, sha256_file
    warnings=[]; sheets=(); counts={}
    if path.suffix.lower() in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        try:
            from openpyxl import load_workbook
            wb=load_workbook(path, read_only=True, keep_vba=True, data_only=False); sheets=tuple(wb.sheetnames); counts["worksheets"]=len(sheets); wb.close()
        except Exception as exc: warnings.append(f"OpenXML 快照读取失败：{exc}")
    else: warnings.append("该格式需要 Excel COM 才能获得完整快照")
    return WorkbookSnapshot(file_id=file_id, source_path=path, sha256=sha256_file(path), sheets=sheets, has_vba=has_vba_project(path), object_counts=counts, warnings=tuple(warnings))
