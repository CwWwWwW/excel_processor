from __future__ import annotations
import time
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from engines.openxml import OpenXmlEngine
class DataFrameEngine:
    name='dataframe'
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        started=time.perf_counter(); op=command.operation
        try:
            import pandas as pd
            if op.opcode=='DEDUP_DATA':
                sheet=op.parameters.get('sheet_name', command.resolved_sheet or 0); header=int(op.parameters.get('header',0)); df=pd.read_excel(command.working_path, sheet_name=sheet, header=header); before=len(df); subset=op.parameters.get('subset')
                keep_mask=~df.duplicated(subset=subset, keep='first'); delete_positions=[i for i, keep in enumerate(keep_mask.tolist()) if not keep]
                excel_rows=[pos + header + 2 for pos in delete_positions]
                if excel_rows:
                    delete_op=op.model_copy(update={'opcode':'DELETE_ROWS','parameters':{'rows':excel_rows}})
                    delete_command=command.model_copy(update={'operation':delete_op, 'selected_engine':EngineMode.OPENXML, 'resolved_sheet': str(sheet) if not isinstance(sheet,int) else command.resolved_sheet})
                    result=OpenXmlEngine().execute(delete_command, context)
                    if not result.success: return result
                return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.DATAFRAME, affected_objects=before-int(keep_mask.sum()), warnings=('DataFrame calculated row changes and wrote them back without rebuilding the worksheet',), duration_ms=int((time.perf_counter()-started)*1000))
            raise ValueError(f'DataFrame engine does not support operation: {op.opcode}')
        except Exception as exc:
            return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.DATAFRAME, errors=(str(exc),), duration_ms=int((time.perf_counter()-started)*1000))
