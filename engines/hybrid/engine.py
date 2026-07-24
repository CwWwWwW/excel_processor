from __future__ import annotations
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from engines.com import ExcelComEngine
from engines.openxml import OpenXmlEngine
class HybridEngine:
    name="hybrid"
    def __init__(self) -> None: self.openxml=OpenXmlEngine(); self.com=ExcelComEngine()
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        if command.operation.opcode in {"SET_VALUE","DELETE_ROWS"} and command.working_path.suffix.lower() in {".xlsx",".xlsm",".xltx",".xltm"}: return self.openxml.execute(command, context)
        if context.capability.get("excel", {}).get("installed"): return self.com.execute(command, context)
        return OperationResult(operation_id=command.operation.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.HYBRID, errors=("当前操作需要 Excel COM，但未检测到可用 Excel",), duration_ms=0)
