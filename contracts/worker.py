from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from excel_processor.version import WORKER_PROTOCOL_VERSION
from .errors import ErrorRecord


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkerRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    protocol_version: str = WORKER_PROTOCOL_VERSION
    message_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    command: str
    file_id: UUID | None = None
    operation_id: UUID | None = None
    timestamp: str = Field(default_factory=utc_timestamp)
    payload: dict[str, Any] = Field(default_factory=dict)


class WorkerResponse(BaseModel):
    model_config = ConfigDict(frozen=True)
    protocol_version: str = WORKER_PROTOCOL_VERSION
    request_message_id: UUID
    job_id: UUID | None = None
    file_id: UUID | None = None
    operation_id: UUID | None = None
    command: str | None = None
    timestamp: str = Field(default_factory=utc_timestamp)
    success: bool
    payload: dict[str, Any] = Field(default_factory=dict)
    error: ErrorRecord | None = None
