from __future__ import annotations
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from .job import EngineMode
from .operation import OperationSpec
class PlannedOperation(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    command: OperationSpec
    resolved_file_ids: tuple[UUID, ...]
    resolved_sheets: tuple[str, ...] = ()
    selected_engine: EngineMode
    dependency_ids: tuple[UUID, ...] = ()
    estimated_changes: int = 0
class ExecutionPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    job_id: UUID
    capability_hash: str
    workbook_snapshot_hashes: dict[UUID, str] = Field(default_factory=dict)
    operations: tuple[PlannedOperation, ...]
    warnings: tuple[str, ...] = ()
class OperationCommand(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    command_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    operation: OperationSpec
    file_id: UUID
    working_path: Path
    output_path: Path | None = None
    selected_engine: EngineMode
    resolved_sheet: str | None = None
    @field_serializer("working_path", "output_path")
    def _sp(self, v: Path | None) -> str | None: return None if v is None else str(v)
class ExecutionContext(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    job_id: UUID
    runtime_root: Path
    capability: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    @field_serializer("runtime_root")
    def _rp(self, v: Path) -> str: return str(v)
