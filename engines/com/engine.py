from __future__ import annotations
import time
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from operations.generic_com.executor import execute_generic_com
from .session import ExcelComSession
class ExcelComEngine:
    name='excel_com'
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        started=time.perf_counter(); workbook=None; op=command.operation
        try:
            with ExcelComSession(False, bool(op.parameters.get('allow_macros', False))) as session:
                workbook=session.open_workbook(command.working_path, False)
                if op.opcode=='SET_VALUE':
                    sheet=workbook.Worksheets.Item(command.resolved_sheet or (op.target.sheet_names or ('Sheet1',))[0]); sheet.Range(op.target.address or op.parameters.get('address')).Value2=op.parameters.get('value'); workbook.Calculate(); workbook.Save()
                elif op.opcode=='SAVE_AS':
                    output=command.output_path or command.working_path; fmt=op.parameters.get('file_format'); workbook.SaveAs(str(output), FileFormat=int(fmt)) if fmt is not None else workbook.SaveAs(str(output))
                elif op.opcode in {'COM_GET','COM_SET','COM_CALL'}: execute_generic_com(workbook, op, allowed_members=set(context.capability.get('typelib_members', {}).get('Application', [])) | set(context.capability.get('runtime_members', []))); workbook.Save()
                else: raise ValueError(f'Excel COM ????????{op.opcode}')
                workbook.Close(SaveChanges=False); workbook=None
            return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.EXCEL_COM, affected_objects=1, duration_ms=int((time.perf_counter()-started)*1000))
        except Exception as exc:
            try:
                if workbook is not None: workbook.Close(SaveChanges=False)
            except Exception as close_exc:
                _ = close_exc
            return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.EXCEL_COM, errors=(str(exc),), duration_ms=int((time.perf_counter()-started)*1000))
