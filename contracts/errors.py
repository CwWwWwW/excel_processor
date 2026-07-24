from __future__ import annotations
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
class ErrorRecord(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    error_id: UUID = Field(default_factory=uuid4)
    job_id: UUID | None = None
    file_id: UUID | None = None
    operation_id: UUID | None = None
    code: str
    message: str
    recoverable: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    details: dict[str, Any] = Field(default_factory=dict)
