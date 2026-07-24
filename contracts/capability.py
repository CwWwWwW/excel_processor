from __future__ import annotations
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_serializer
class ExcelInstallation(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    installed: bool = False
    display_name: str = "Microsoft Excel not detected"
    com_version: str | None = None
    build: str | None = None
    file_version: str | None = None
    executable: Path | None = None
    operating_system: str | None = None
    product_release_ids: str | None = None
    version_to_report: str | None = None
    platform: str | None = None
    update_channel: str | None = None
    bitness: str | None = None
    error: str | None = None
    @field_serializer("executable")
    def _ep(self, v: Path | None) -> str | None: return None if v is None else str(v)
class FileFormatCapability(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    menu_name: str
    extension: str
    file_format: int | None = None
    category: str = "workbook"
    can_preserve_vba: bool = False
    may_lose_objects: bool = False
    min_com_version: str | None = None
class CapabilityProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = "1.0"
    excel: ExcelInstallation = Field(default_factory=ExcelInstallation)
    supported_file_formats: tuple[FileFormatCapability, ...] = ()
    typelib_members: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    available_addins: tuple[str, ...] = ()
    vba_project_access: bool = False
    power_query_available: bool = False
    data_model_available: bool = False
    macro_execution_allowed: bool = False
    default_engine: str = "hybrid"
    raw: dict[str, Any] = Field(default_factory=dict)
    def capability_hash_source(self) -> str:
        return self.model_dump_json(exclude={"raw"})
