from __future__ import annotations
from enum import StrEnum
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from excel_processor.version import CONTRACTS_SCHEMA_VERSION

class ErrorPolicy(StrEnum):
    STOP_JOB="stop_job"; SKIP_FILE="skip_file"; SKIP_SHEET="skip_sheet"; SKIP_OPERATION="skip_operation"; SKIP_ROW="skip_row"; CONTINUE="continue"
class EngineMode(StrEnum):
    AUTO="auto"; EXCEL_COM="excel_com"; OPENXML="openxml"; DATAFRAME="dataframe"; HYBRID="hybrid"
class AtomicityMode(StrEnum):
    JOB="job"; FILE="file"
class FileSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    file_id: UUID = Field(default_factory=uuid4)
    source_path: Path
    expected_password: str | None = Field(default=None, exclude=True)
    write_password: str | None = Field(default=None, exclude=True)
    read_only: bool = False
    @field_serializer("source_path")
    def _sp(self, v: Path) -> str: return str(v)
class OutputSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    output_directory: Path
    filename_template: str = "${file_stem}_processed"
    format_code: int | None = None
    preserve_source_format: bool = True
    overwrite_policy: Literal["reject","rename","replace_after_backup"] = "rename"
    compatibility_baseline: str = "auto"
    allow_warnings: bool = False
    @field_serializer("output_directory")
    def _op(self, v: Path) -> str: return str(v)
class JobSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    job_id: UUID = Field(default_factory=uuid4)
    name: str
    files: tuple[FileSpec, ...]
    operations: tuple["OperationSpec", ...]
    output: OutputSpec
    engine_mode: EngineMode = EngineMode.AUTO
    atomicity_mode: AtomicityMode = AtomicityMode.JOB
    preview_only: bool = False
