from __future__ import annotations
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from excel_processor.version import CONTRACTS_SCHEMA_VERSION
from .job import EngineMode, ErrorPolicy
class TargetSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    file_ids: tuple[UUID, ...] | None = None
    file_name_pattern: str | None = None
    sheet_names: tuple[str, ...] | None = None
    sheet_name_pattern: str | None = None
    sheet_type: str | None = None
    address: str | None = None
    table_name: str | None = None
    named_range: str | None = None
    header_name: str | None = None
    object_chain: tuple[dict[str, Any], ...] = ()
class ConditionExpr(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    operator: str
    field: str | None = None
    value: Any = None
    children: tuple["ConditionExpr", ...] = ()
class ValidationSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    validator: str
    parameters: dict[str, Any] = Field(default_factory=dict)
class OperationSpec(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    operation_id: UUID = Field(default_factory=uuid4)
    opcode: str
    target: TargetSpec
    condition: ConditionExpr | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    engine_hint: EngineMode = EngineMode.AUTO
    required_capabilities: frozenset[str] = Field(default_factory=frozenset)
    depends_on: tuple[UUID, ...] = ()
    validations: tuple[ValidationSpec, ...] = ()
    error_policy: ErrorPolicy = ErrorPolicy.STOP_JOB
    enabled: bool = True
