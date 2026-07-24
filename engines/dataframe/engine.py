from __future__ import annotations
import time
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
class DataFrameEngine:
    name="dataframe"
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        started=time.perf_counter(); op=command.operation
        try:
            import pandas as pd
            if op.opcode=="DEDUP_DATA":
                sheet=op.parameters.get("sheet_name", command.resolved_sheet or 0); df=pd.read_excel(command.working_path, sheet_name=sheet); before=len(df); df=df.drop_duplicates(subset=op.parameters.get("subset"))
                with pd.ExcelWriter(command.working_path, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer: df.to_excel(writer, index=False, sheet_name=str(sheet) if not isinstance(sheet,int) else "Sheet1")
                return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.DATAFRAME, affected_objects=before-len(df), duration_ms=int((time.perf_counter()-started)*1000))
            raise ValueError(f"DataFrame 引擎不支持操作：{op.opcode}")
        except Exception as exc: return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.DATAFRAME, errors=(str(exc),), duration_ms=int((time.perf_counter()-started)*1000))
