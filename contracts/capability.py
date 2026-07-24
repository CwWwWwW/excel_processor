from __future__ import annotations
from pathlib import Path
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from excel_processor.version import CONTRACTS_SCHEMA_VERSION
from .job import EngineMode

class ExcelInstallation(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    installed: bool = False
    display_name: str = "Microsoft Excel not detected"
    support_level: str = "none"
    com_version: str | None = None
    build: str | None = None
    file_version: str | None = None
    executable: Path | None = None
    operating_system: str | None = None
    product_release_ids: str | None = None
    version_to_report: str | None = None
    platform: str | None = None
    update_channel: str | None = None
    msi_product_name: str | None = None
    app_paths_executable: Path | None = None
    bitness: str | None = None
    hwnd: int | None = None
    process_id: int | None = None
    error: str | None = None
    @field_serializer("executable", "app_paths_executable")
    def _path(self, v: Path | None) -> str | None: return None if v is None else str(v)

class FileFormatCapability(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    menu_name: str
    extension: str
    file_format: int | None = None
    category: str = "workbook"
    can_preserve_vba: bool = False
    may_lose_objects: bool = False
    min_com_version: str | None = None

class PlatformProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    windows_name: str = "Unknown Windows"
    windows_version: str = ""
    windows_build: int = 0
    service_pack: str | None = None
    architecture: str = "unknown"
    runtime_family: str = "modern-x64"
    excel: ExcelInstallation = Field(default_factory=ExcelInstallation)
    capabilities: frozenset[str] = Field(default_factory=frozenset)

class EngineDecision(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    supported: bool
    engine: EngineMode | None = None
    reason: str
    required_capabilities: frozenset[str] = Field(default_factory=frozenset)
    fidelity_risk: str | None = None

class CapabilityProfile(BaseModel):
    model_config = ConfigDict(frozen=True)
    schema_version: str = CONTRACTS_SCHEMA_VERSION
    excel: ExcelInstallation = Field(default_factory=ExcelInstallation)
    platform: PlatformProfile | None = None
    supported_file_formats: tuple[FileFormatCapability, ...] = ()
    typelib_members: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    runtime_members: frozenset[str] = Field(default_factory=frozenset)
    available_addins: tuple[str, ...] = ()
    vba_project_access: bool = False
    power_query_available: bool = False
    data_model_available: bool = False
    macro_execution_allowed: bool = False
    default_engine: str = "hybrid"
    raw: dict[str, Any] = Field(default_factory=dict)
    def capability_hash_source(self) -> str:
        return self.model_dump_json(exclude={"raw"})
