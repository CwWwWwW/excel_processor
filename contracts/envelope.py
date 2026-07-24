from __future__ import annotations
from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field
from excel_processor.version import CONTRACTS_SCHEMA_VERSION
T = TypeVar("T")
class Envelope(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    message_id: UUID = Field(default_factory=uuid4)
    job_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    producer: str
    payload: T
