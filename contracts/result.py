from __future__ import annotations
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from excel_processor.version import CONTRACTS_SCHEMA_VERSION
from .job import EngineMode
class ChangeRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    file_id: UUID
    sheet_name: str | None = None
    address: str | None = None
    object_type: str
    field_name: str | None = None
    old_value: Any = None
    new_value: Any = None
class OperationResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    operation_id: UUID
    file_id: UUID
    success: bool
    engine_used: EngineMode
    affected_objects: int = 0
    changes: tuple[ChangeRecord, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    duration_ms: int = 0
class CandidateArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    artifact_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    file_id: UUID
    candidate_path: Path
    sha256: str
    size_bytes: int
    @field_serializer("candidate_path")
    def _cp(self, v: Path) -> str: return str(v)
class VerificationStatus(StrEnum):
    PASS="PASS"; PASS_WITH_WARNINGS="PASS_WITH_WARNINGS"; REJECTED="REJECTED"
class VerificationReport(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    report_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    file_id: UUID | None = None
    status: VerificationStatus
    checks: dict[str, bool] = Field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
class TransactionRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    transaction_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    file_id: UUID | None = None
    stage: str
    path: Path | None = None
    sha256: str | None = None
    message: str = ""
    @field_serializer("path")
    def _path(self, v: Path | None) -> str | None: return None if v is None else str(v)
class JobResult(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    job_id: UUID
    success: bool
    artifacts: tuple[CandidateArtifact, ...] = ()
    reports: tuple[VerificationReport, ...] = ()
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
