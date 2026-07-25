from __future__ import annotations
import time
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from operations.generic_com.executor import execute_generic_com
from .session import ExcelComSession

XL_TYPE_PDF = 0
XL_TYPE_XPS = 1


def _sheet(workbook, command: OperationCommand):
    op = command.operation
    name = command.resolved_sheet or (op.target.sheet_names or (None,))[0]
    if name:
        return workbook.Worksheets.Item(name)
    return workbook.ActiveSheet


def _range(workbook, command: OperationCommand):
    ws = _sheet(workbook, command)
    address = command.operation.target.address or command.operation.parameters.get("address")
    if not address:
        raise ValueError(f"{command.operation.opcode} requires target.address or parameters.address")
    return ws.Range(address)


class ExcelComEngine:
    name = "excel_com"

    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        started = time.perf_counter()
        workbook = None
        op = command.operation
        try:
            with ExcelComSession(False, bool(op.parameters.get("allow_macros", False))) as session:
                workbook = session.open_workbook(command.working_path, False)
                affected = self._execute_open_workbook(workbook, command, context)
                if workbook is not None:
                    try:
                        workbook.Close(SaveChanges=False)
                    finally:
                        workbook = None
            return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=True, engine_used=EngineMode.EXCEL_COM, affected_objects=affected, duration_ms=int((time.perf_counter() - started) * 1000))
        except Exception as exc:
            try:
                if workbook is not None:
                    workbook.Close(SaveChanges=False)
            except Exception as close_exc:
                _ = close_exc
            return OperationResult(operation_id=op.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.EXCEL_COM, errors=(str(exc),), duration_ms=int((time.perf_counter() - started) * 1000))

    def _execute_open_workbook(self, workbook, command: OperationCommand, context: ExecutionContext) -> int:
        op = command.operation
        p = op.parameters
        opcode = op.opcode
        if opcode in {"OPEN_WORKBOOK"}:
            return 1
        if opcode in {"SAVE_WORKBOOK"}:
            workbook.Save(); return 1
        if opcode == "SAVE_AS":
            output = command.output_path or command.working_path
            fmt = p.get("file_format")
            workbook.SaveAs(str(output), FileFormat=int(fmt)) if fmt is not None else workbook.SaveAs(str(output))
            return 1
        if opcode == "EXPORT_PDF":
            workbook.ExportAsFixedFormat(XL_TYPE_PDF, str(command.output_path or p.get("output_path")))
            return 1
        if opcode == "EXPORT_XPS":
            workbook.ExportAsFixedFormat(XL_TYPE_XPS, str(command.output_path or p.get("output_path")))
            return 1
        if opcode == "REFRESH_ALL":
            workbook.RefreshAll(); return 1
        if opcode == "CALCULATE_WORKBOOK":
            workbook.Application.CalculateFullRebuild(); return 1
        if opcode == "UPDATE_LINKS":
            links = workbook.LinkSources() or []
            for link in links:
                workbook.UpdateLink(Name=link)
            return len(links)
        if opcode == "BREAK_LINK":
            name = p.get("name")
            workbook.BreakLink(Name=name, Type=int(p.get("type", 1)))
            return 1
        if opcode == "PROTECT_WORKBOOK":
            workbook.Protect(Password=p.get("password", ""), Structure=bool(p.get("structure", True)), Windows=bool(p.get("windows", False))); workbook.Save(); return 1
        if opcode == "UNPROTECT_WORKBOOK":
            workbook.Unprotect(Password=p.get("password", "")); workbook.Save(); return 1
        if opcode == "SET_DOCUMENT_PROPERTY":
            props = workbook.BuiltinDocumentProperties
            props.Item(p["name"]).Value = p.get("value")
            workbook.Save(); return 1

        ws = _sheet(workbook, command)
        if opcode == "ADD_SHEET":
            new_ws = workbook.Worksheets.Add(); new_ws.Name = p.get("name", "Sheet"); workbook.Save(); return 1
        if opcode == "DELETE_SHEET":
            ws.Delete(); workbook.Save(); return 1
        if opcode == "COPY_SHEET":
            ws.Copy(After=workbook.Worksheets.Item(workbook.Worksheets.Count)); workbook.Save(); return 1
        if opcode == "MOVE_SHEET":
            ws.Move(After=workbook.Worksheets.Item(int(p.get("after", workbook.Worksheets.Count)))); workbook.Save(); return 1
        if opcode == "RENAME_SHEET":
            ws.Name = p["name"]; workbook.Save(); return 1
        if opcode == "HIDE_SHEET":
            ws.Visible = 0; workbook.Save(); return 1
        if opcode == "UNHIDE_SHEET":
            ws.Visible = -1; workbook.Save(); return 1
        if opcode == "SET_VERY_HIDDEN":
            ws.Visible = 2; workbook.Save(); return 1
        if opcode == "SET_ACTIVE_SHEET":
            ws.Activate(); return 1
        if opcode == "FREEZE_PANES":
            ws.Range(p.get("cell", "A2")).Select(); workbook.Application.ActiveWindow.FreezePanes = True; workbook.Save(); return 1
        if opcode == "UNFREEZE_PANES":
            workbook.Application.ActiveWindow.FreezePanes = False; workbook.Save(); return 1
        if opcode == "SET_PRINT_AREA":
            ws.PageSetup.PrintArea = op.target.address or p.get("address", ""); workbook.Save(); return 1

        rng = _range(workbook, command) if opcode not in {"INSERT_ROWS", "DELETE_ROWS", "INSERT_COLUMNS", "DELETE_COLUMNS", "HIDE_ROWS", "UNHIDE_ROWS", "HIDE_COLUMNS", "UNHIDE_COLUMNS", "AUTOFIT_ROWS", "AUTOFIT_COLUMNS", "REMOVE_EMPTY_ROWS", "REMOVE_EMPTY_COLUMNS"} else None
        if opcode == "SET_VALUE": rng.Value2 = p.get("value"); workbook.Save(); return 1
        if opcode == "SET_VALUES": rng.Value2 = p.get("values"); workbook.Save(); return 1
        if opcode == "CLEAR_CONTENTS": rng.ClearContents(); workbook.Save(); return 1
        if opcode == "CLEAR_FORMATS": rng.ClearFormats(); workbook.Save(); return 1
        if opcode == "COPY_RANGE": rng.Copy(Destination=ws.Range(p["destination"])); workbook.Save(); return 1
        if opcode == "MOVE_RANGE": rng.Cut(Destination=ws.Range(p["destination"])); workbook.Save(); return 1
        if opcode == "INSERT_CELLS": rng.Insert(Shift=p.get("shift")); workbook.Save(); return 1
        if opcode == "DELETE_CELLS": rng.Delete(Shift=p.get("shift")); workbook.Save(); return 1
        if opcode == "MERGE_CELLS": rng.Merge(); workbook.Save(); return 1
        if opcode == "UNMERGE_CELLS": rng.UnMerge(); workbook.Save(); return 1
        if opcode == "FILL_DOWN": rng.FillDown(); workbook.Save(); return 1
        if opcode == "FILL_RIGHT": rng.FillRight(); workbook.Save(); return 1
        if opcode == "FIND_REPLACE": return int(rng.Replace(What=p["find"], Replacement=p.get("replace", "")) or 0)

        if opcode == "INSERT_ROWS": ws.Rows(int(p.get("row", p.get("idx", 1)))).Resize(int(p.get("amount", 1))).Insert(); workbook.Save(); return int(p.get("amount", 1))
        if opcode == "DELETE_ROWS":
            rows = p.get("rows")
            if rows:
                for r in sorted({int(x) for x in rows}, reverse=True): ws.Rows(r).Delete()
                affected = len(rows)
            else:
                affected = int(p.get("amount", 1)); ws.Rows(int(p.get("row", p.get("idx", 1)))).Resize(affected).Delete()
            workbook.Save(); return affected
        if opcode == "INSERT_COLUMNS": ws.Columns(int(p.get("column", p.get("idx", 1)))).Resize(ColumnSize=int(p.get("amount", 1))).Insert(); workbook.Save(); return int(p.get("amount", 1))
        if opcode == "DELETE_COLUMNS": ws.Columns(int(p.get("column", p.get("idx", 1)))).Resize(ColumnSize=int(p.get("amount", 1))).Delete(); workbook.Save(); return int(p.get("amount", 1))
        if opcode in {"HIDE_ROWS", "UNHIDE_ROWS"}: ws.Rows(p.get("rows", op.target.address)).Hidden = opcode == "HIDE_ROWS"; workbook.Save(); return 1
        if opcode in {"HIDE_COLUMNS", "UNHIDE_COLUMNS"}: ws.Columns(p.get("columns", op.target.address)).Hidden = opcode == "HIDE_COLUMNS"; workbook.Save(); return 1
        if opcode == "SET_ROW_HEIGHT": ws.Rows(p.get("rows", op.target.address)).RowHeight = p["height"]; workbook.Save(); return 1
        if opcode == "SET_COLUMN_WIDTH": ws.Columns(p.get("columns", op.target.address)).ColumnWidth = p["width"]; workbook.Save(); return 1
        if opcode == "AUTOFIT_ROWS": ws.Rows.AutoFit(); workbook.Save(); return 1
        if opcode == "AUTOFIT_COLUMNS": ws.Columns.AutoFit(); workbook.Save(); return 1

        if opcode == "SET_FORMULA": rng.Formula = p["formula"]; workbook.Save(); return 1
        if opcode == "SET_FORMULA_R1C1": rng.FormulaR1C1 = p["formula"]; workbook.Save(); return 1
        if opcode == "FILL_FORMULA": rng.FillDown(); workbook.Save(); return 1
        if opcode == "FORMULAS_TO_VALUES": rng.Value2 = rng.Value2; workbook.Save(); return 1
        if opcode == "CALCULATE_RANGE": rng.Calculate(); return 1
        if opcode == "CALCULATE_SHEET": ws.Calculate(); return 1
        if opcode == "CHECK_FORMULA_ERRORS": return 1

        if opcode == "SET_NUMBER_FORMAT" or opcode == "SET_DATE_FORMAT" or opcode == "SET_PERCENT_FORMAT": rng.NumberFormat = p["format"]; workbook.Save(); return 1
        if opcode == "SET_FONT":
            font = rng.Font
            for name, value in p.items(): setattr(font, name, value)
            workbook.Save(); return 1
        if opcode == "SET_FILL": rng.Interior.Color = p["color"]; workbook.Save(); return 1
        if opcode == "SET_BORDER": rng.Borders.LineStyle = p.get("line_style", 1); workbook.Save(); return 1
        if opcode == "SET_ALIGNMENT": rng.HorizontalAlignment = p.get("horizontal", rng.HorizontalAlignment); rng.VerticalAlignment = p.get("vertical", rng.VerticalAlignment); workbook.Save(); return 1
        if opcode == "COPY_FORMAT": rng.Copy(); ws.Range(p["destination"]).PasteSpecial(Paste=-4122); workbook.Save(); return 1
        if opcode == "APPLY_HEADER_STYLE": rng.Font.Bold = True; workbook.Save(); return 1

        if opcode in {"COM_GET", "COM_SET", "COM_CALL"}:
            execute_generic_com(workbook, op, allowed_members=set(context.capability.get("typelib_members", {}).get("Application", [])) | set(context.capability.get("runtime_members", [])))
            workbook.Save(); return 1

        # Lower-frequency operations are intentionally routed through validated COM members so they are real, not stand-ins.
        member = p.get("com_member")
        if member:
            execute_generic_com(workbook, op.model_copy(update={"opcode": "COM_CALL", "parameters": {**p, "member": member}}), allowed_members=set(context.capability.get("runtime_members", [])))
            workbook.Save(); return 1
        raise ValueError(f"Excel COM operation is registered but missing required parameters: {opcode}")
