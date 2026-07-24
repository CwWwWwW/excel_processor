from __future__ import annotations
import shutil, time
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import ChangeRecord, OperationResult
class OpenXmlEngine:
    name="openxml"
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        started=time.perf_counter(); op=command.operation
        try:
            from openpyxl import load_workbook
            if op.opcode=="SET_VALUE":
                wb=load_workbook(command.working_path, keep_vba=True); ws=wb[command.resolved_sheet or (op.target.sheet_names or (wb.sheetnames[0],))[0]]; addr=op.target.address or op.parameters.get("address")
                if not addr: raise ValueError("SET_VALUE 需要 target.address 或 parameters.address")
                old=ws[addr].value; new=op.parameters.get("value"); ws[addr]=new; wb.save(command.working_path); wb.close()
                return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.OPENXML, affected_objects=1, changes=(ChangeRecord(file_id=command.file_id, sheet_name=ws.title, address=addr, object_type="cell", field_name="value", old_value=old, new_value=new),), duration_ms=int((time.perf_counter()-started)*1000))
            if op.opcode=="DELETE_ROWS":
                wb=load_workbook(command.working_path, keep_vba=True); ws=wb[command.resolved_sheet or (op.target.sheet_names or (wb.sheetnames[0],))[0]]; idx=int(op.parameters.get("idx", op.parameters.get("row",1))); amount=int(op.parameters.get("amount",1)); ws.delete_rows(idx, amount); wb.save(command.working_path); wb.close()
                return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.OPENXML, affected_objects=amount, duration_ms=int((time.perf_counter()-started)*1000))
            if op.opcode=="SAVE_AS" and command.output_path: shutil.copy2(command.working_path, command.output_path); return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.OPENXML, affected_objects=1, warnings=("OpenXML 保存未执行 Excel 重算，最终验证阶段需要 COM 重开时会再次校验",), duration_ms=int((time.perf_counter()-started)*1000))
            raise ValueError(f"OpenXML 引擎不支持操作：{op.opcode}")
        except Exception as exc:
            return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.OPENXML, errors=(str(exc),), duration_ms=int((time.perf_counter()-started)*1000))
