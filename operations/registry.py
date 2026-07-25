from __future__ import annotations
from dataclasses import dataclass, field
from typing import Protocol
from contracts.capability import CapabilityProfile, EngineDecision
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult, VerificationReport
from discovery.workbook_inspector import WorkbookSnapshot


class OperationHandler(Protocol):
    opcode: str
    def validate(self, command: OperationCommand, capability: CapabilityProfile, snapshot: WorkbookSnapshot | None = None) -> tuple[str, ...]: ...
    def resolve_engine(self, command: OperationCommand, capability: CapabilityProfile, snapshot: WorkbookSnapshot | None = None) -> EngineDecision: ...
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult: ...
    def verify(self, command: OperationCommand, result: OperationResult, snapshot_after: WorkbookSnapshot | None = None) -> tuple[str, ...]: ...


@dataclass(frozen=True)
class OperationMetadata:
    opcode: str
    handler_class: str
    implemented: bool = True
    parameter_schema: dict = field(default_factory=dict)
    supported_engines: tuple[str, ...] = ("excel_com",)
    supported_file_formats: tuple[str, ...] = ("xlsx", "xlsm", "xlsb", "xls")
    minimum_excel_version: str = "2007"
    required_com_members: tuple[str, ...] = ()
    requires_excel: bool = False
    preserves_vba: bool = True
    supports_skip_row: bool = False
    validators: tuple[str, ...] = ("handler.validate", "handler.verify")
    tests: tuple[str, ...] = ()
    category: str = "general"
    chinese_name: str = "Excel ??"


class OperationRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, OperationHandler] = {}
        self._metadata: dict[str, OperationMetadata] = {}

    def register(self, handler: OperationHandler, metadata: OperationMetadata | None = None) -> None:
        if handler.opcode in self._handlers:
            raise ValueError(f"Duplicate operation opcode: {handler.opcode}")
        self._handlers[handler.opcode] = handler
        self._metadata[handler.opcode] = metadata or OperationMetadata(opcode=handler.opcode, handler_class=f"{handler.__class__.__module__}.{handler.__class__.__name__}")

    def get(self, opcode: str) -> OperationHandler:
        try:
            return self._handlers[opcode]
        except KeyError as exc:
            raise ValueError(f"Unregistered operation: {opcode}") from exc

    def get_metadata(self, opcode: str) -> OperationMetadata:
        try:
            return self._metadata[opcode]
        except KeyError as exc:
            raise ValueError(f"Unregistered operation metadata: {opcode}") from exc

    def list_opcodes(self) -> tuple[str, ...]:
        return tuple(sorted(self._handlers))

    def catalog(self) -> list[dict]:
        return [self._metadata[opcode].__dict__ | {"opcode": opcode} for opcode in self.list_opcodes()]
