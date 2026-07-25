from __future__ import annotations
from dataclasses import dataclass

from contracts.capability import CapabilityProfile, EngineDecision
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from discovery.workbook_inspector import WorkbookSnapshot
from engines.dataframe import DataFrameEngine
from engines.hybrid import HybridEngine
from engines.openxml import OpenXmlEngine
from engines.router import EngineRouter
from .registry import OperationMetadata, OperationRegistry


@dataclass(frozen=True)
class EngineBackedHandler:
    opcode: str
    category: str = "standard"
    chinese_name: str = "Excel ??"
    supported_engines: tuple[EngineMode, ...] = (EngineMode.HYBRID,)
    requires_excel: bool = False
    supports_skip_row: bool = False
    required_com_members: tuple[str, ...] = ()

    def validate(self, command: OperationCommand, capability: CapabilityProfile, snapshot: WorkbookSnapshot | None = None) -> tuple[str, ...]:
        errors: list[str] = []
        if command.operation.opcode != self.opcode:
            errors.append("Operation opcode does not match handler")
        if command.operation.error_policy.value == "skip_row" and not self.supports_skip_row:
            errors.append(f"{self.opcode} does not support SKIP_ROW")
        if self.requires_excel and not capability.excel.installed:
            errors.append("This operation requires Excel COM, but Excel is not installed")
        if self.opcode in {"SET_VALUE", "SET_VALUES"} and not (command.operation.target.address or command.operation.parameters.get("address")):
            errors.append("SET_VALUE/SET_VALUES requires target.address or parameters.address")
        return tuple(errors)

    def resolve_engine(self, command: OperationCommand, capability: CapabilityProfile, snapshot: WorkbookSnapshot | None = None) -> EngineDecision:
        return EngineRouter().decide(command.operation, capability, snapshot)

    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        if command.selected_engine == EngineMode.EXCEL_COM:
            return OperationResult(operation_id=command.operation.operation_id, file_id=command.file_id, success=False, engine_used=EngineMode.EXCEL_COM, errors=("Excel COM operations must execute through ExcelWorkerClient",))
        engines = {EngineMode.OPENXML: OpenXmlEngine(), EngineMode.DATAFRAME: DataFrameEngine(), EngineMode.HYBRID: HybridEngine()}
        engine = engines.get(command.selected_engine)
        if engine is None:
            return OperationResult(operation_id=command.operation.operation_id, file_id=command.file_id, success=False, engine_used=command.selected_engine, errors=(f"No local engine for {command.selected_engine}",))
        return engine.execute(command, context)

    def verify(self, command: OperationCommand, result: OperationResult, snapshot_after: WorkbookSnapshot | None = None) -> tuple[str, ...]:
        return tuple(result.errors)


_OPERATION_GROUPS = {
    "workbook": ["OPEN_WORKBOOK", "SAVE_WORKBOOK", "SAVE_AS", "EXPORT_PDF", "EXPORT_XPS", "REFRESH_ALL", "CALCULATE_WORKBOOK", "UPDATE_LINKS", "BREAK_LINK", "PROTECT_WORKBOOK", "UNPROTECT_WORKBOOK", "SET_DOCUMENT_PROPERTY"],
    "worksheet": ["ADD_SHEET", "DELETE_SHEET", "COPY_SHEET", "MOVE_SHEET", "RENAME_SHEET", "HIDE_SHEET", "UNHIDE_SHEET", "SET_VERY_HIDDEN", "SET_ACTIVE_SHEET", "FREEZE_PANES", "UNFREEZE_PANES", "SET_PRINT_AREA"],
    "range": ["SET_VALUE", "SET_VALUES", "CLEAR_CONTENTS", "CLEAR_FORMATS", "COPY_RANGE", "MOVE_RANGE", "INSERT_CELLS", "DELETE_CELLS", "MERGE_CELLS", "UNMERGE_CELLS", "FILL_DOWN", "FILL_RIGHT", "FIND_REPLACE"],
    "rows_columns": ["INSERT_ROWS", "DELETE_ROWS", "INSERT_COLUMNS", "DELETE_COLUMNS", "HIDE_ROWS", "UNHIDE_ROWS", "HIDE_COLUMNS", "UNHIDE_COLUMNS", "SET_ROW_HEIGHT", "SET_COLUMN_WIDTH", "AUTOFIT_ROWS", "AUTOFIT_COLUMNS", "REMOVE_EMPTY_ROWS", "REMOVE_EMPTY_COLUMNS"],
    "data": ["SORT_RANGE", "FILTER_RANGE", "REMOVE_DUPLICATES", "DEDUP_DATA", "FILL_EMPTY", "REPLACE_VALUES", "SPLIT_COLUMN", "MERGE_COLUMNS", "JOIN_TABLES", "APPEND_TABLES", "GROUP_AGGREGATE", "PIVOT_DATA", "UNPIVOT_DATA", "TRANSPOSE_DATA"],
    "formula": ["SET_FORMULA", "SET_FORMULA_R1C1", "FILL_FORMULA", "FORMULAS_TO_VALUES", "CALCULATE_RANGE", "CALCULATE_SHEET", "CHECK_FORMULA_ERRORS"],
    "format": ["SET_FONT", "SET_FILL", "SET_BORDER", "SET_ALIGNMENT", "SET_NUMBER_FORMAT", "SET_DATE_FORMAT", "SET_PERCENT_FORMAT", "COPY_FORMAT", "APPLY_HEADER_STYLE"],
    "validation": ["ADD_CONDITIONAL_FORMAT", "DELETE_CONDITIONAL_FORMAT", "ADD_DATA_VALIDATION", "DELETE_DATA_VALIDATION"],
    "table": ["CREATE_TABLE", "RESIZE_TABLE", "DELETE_TABLE", "ADD_TABLE_ROW", "DELETE_TABLE_ROW", "ADD_TABLE_COLUMN", "DELETE_TABLE_COLUMN"],
    "name": ["ADD_DEFINED_NAME", "UPDATE_DEFINED_NAME", "DELETE_DEFINED_NAME"],
    "chart_pivot": ["CREATE_CHART", "DELETE_CHART", "UPDATE_CHART_SOURCE", "CREATE_PIVOT_TABLE", "REFRESH_PIVOT_TABLE", "DELETE_PIVOT_TABLE"],
    "media": ["INSERT_IMAGE", "DELETE_IMAGE", "ADD_COMMENT", "DELETE_COMMENT", "ADD_HYPERLINK", "DELETE_HYPERLINK"],
    "generic_com": ["COM_GET", "COM_SET", "COM_CALL"],
}

_OPENXML_SAFE = {"SET_VALUE", "SET_VALUES", "DELETE_ROWS", "INSERT_ROWS", "DELETE_COLUMNS", "INSERT_COLUMNS", "CLEAR_CONTENTS", "CLEAR_FORMATS", "DEDUP_DATA"}
_DATAFRAME = {"DEDUP_DATA", "REMOVE_DUPLICATES", "JOIN_TABLES", "APPEND_TABLES", "GROUP_AGGREGATE", "PIVOT_DATA", "UNPIVOT_DATA", "TRANSPOSE_DATA", "SORT_RANGE", "FILTER_RANGE", "FILL_EMPTY", "REPLACE_VALUES", "SPLIT_COLUMN", "MERGE_COLUMNS"}
_COM_REQUIRED = set().union(*_OPERATION_GROUPS.values()) - _OPENXML_SAFE - _DATAFRAME
_COM_REQUIRED.update({"SAVE_AS", "EXPORT_PDF", "EXPORT_XPS", "COM_GET", "COM_SET", "COM_CALL"})


def _metadata(opcode: str, category: str, handler: EngineBackedHandler) -> OperationMetadata:
    engines = tuple(e.value for e in handler.supported_engines)
    return OperationMetadata(
        opcode=opcode,
        handler_class=f"{handler.__class__.__module__}.{handler.__class__.__name__}",
        implemented=True,
        parameter_schema={"type": "object", "additionalProperties": True},
        supported_engines=engines,
        supported_file_formats=("xlsx", "xlsm", "xlsb", "xls", "xltx", "xltm", "csv", "txt") if opcode.startswith("COM_") else ("xlsx", "xlsm", "xlsb", "xls"),
        minimum_excel_version="2007",
        required_com_members=handler.required_com_members,
        requires_excel=handler.requires_excel,
        preserves_vba=opcode not in {"SAVE_AS", "EXPORT_PDF", "EXPORT_XPS"},
        supports_skip_row=handler.supports_skip_row,
        tests=("tests/unit/test_router_registry.py",),
        category=category,
        chinese_name=handler.chinese_name,
    )


def build_default_registry() -> OperationRegistry:
    registry = OperationRegistry()
    for category, opcodes in _OPERATION_GROUPS.items():
        for opcode in opcodes:
            engines: tuple[EngineMode, ...]
            if opcode in _DATAFRAME:
                engines = (EngineMode.DATAFRAME, EngineMode.OPENXML, EngineMode.EXCEL_COM)
            elif opcode in _OPENXML_SAFE:
                engines = (EngineMode.HYBRID, EngineMode.OPENXML, EngineMode.EXCEL_COM)
            else:
                engines = (EngineMode.EXCEL_COM,)
            handler = EngineBackedHandler(
                opcode=opcode,
                category=category,
                chinese_name=opcode.replace("_", " ").title(),
                supported_engines=engines,
                requires_excel=opcode in _COM_REQUIRED,
                supports_skip_row=opcode in {"DEDUP_DATA", "REMOVE_DUPLICATES", "FILL_EMPTY", "REPLACE_VALUES"},
                required_com_members=("Workbooks", "Worksheets", "Range") if opcode in _COM_REQUIRED else (),
            )
            registry.register(handler, _metadata(opcode, category, handler))
    return registry
