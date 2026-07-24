from __future__ import annotations
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from excel_processor.version import CONTRACTS_SCHEMA_VERSION
from .job import ErrorPolicy
class ErrorAction(StrEnum):
    STOP_JOB="stop_job"; SKIP_FILE="skip_file"; SKIP_SHEET="skip_sheet"; SKIP_OPERATION="skip_operation"; SKIP_ROW="skip_row"; CONTINUE="continue"
class ErrorRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    error_id: UUID = Field(default_factory=uuid4)
    job_id: UUID | None = None
    file_id: UUID | None = None
    operation_id: UUID | None = None
    sheet_name: str | None = None
    code: str
    message: str
    recoverable: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    details: dict[str, Any] = Field(default_factory=dict)
class ErrorDecision(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    action: ErrorAction
    record: ErrorRecord
    should_continue_job: bool
    should_continue_file: bool
    should_continue_sheet: bool
    should_continue_operation: bool
class ErrorDecider:
    def decide(self, policy: ErrorPolicy, record: ErrorRecord) -> ErrorDecision:
        action = ErrorAction(policy.value)
        return ErrorDecision(
            action=action,
            record=record,
            should_continue_job=policy != ErrorPolicy.STOP_JOB,
            should_continue_file=policy not in {ErrorPolicy.STOP_JOB, ErrorPolicy.SKIP_FILE},
            should_continue_sheet=policy not in {ErrorPolicy.STOP_JOB, ErrorPolicy.SKIP_FILE, ErrorPolicy.SKIP_SHEET},
            should_continue_operation=policy in {ErrorPolicy.CONTINUE, ErrorPolicy.SKIP_ROW},
        )
