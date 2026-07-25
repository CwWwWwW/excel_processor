from __future__ import annotations
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from engines.openxml import OpenXmlEngine


class HybridEngine:
    name = "hybrid"

    def __init__(self) -> None:
        self.openxml = OpenXmlEngine()

    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        if command.operation.opcode in {"SET_VALUE", "DELETE_ROWS"} and command.working_path.suffix.lower() in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
            return self.openxml.execute(command, context)
        return OperationResult(
            operation_id=command.operation.operation_id,
            file_id=command.file_id,
            success=False,
            engine_used=EngineMode.HYBRID,
            errors=("This operation requires Excel COM and must be routed through the Excel worker process",),
            duration_ms=0,
        )
