from __future__ import annotations
from contracts.capability import CapabilityProfile, EngineDecision
from contracts.job import EngineMode
from contracts.operation import OperationSpec
from discovery.workbook_inspector import WorkbookSnapshot

COM_PREFIXES = ("PIVOT_", "CHART_", "VBA_", "CONNECTION_", "POWER_QUERY_", "PRINT_", "COM_", "SAVE_AS", "EXPORT_", "REFRESH_", "UPDATE_LINKS", "BREAK_LINK", "PROTECT_", "UNPROTECT_", "SET_DOCUMENT_PROPERTY")
DATAFRAME_PREFIXES = ("JOIN_", "GROUP_", "FILTER_DATA_", "PIVOT_DATA", "DEDUP_", "CLEAN_TEXT", "SORT_RANGE", "FILTER_RANGE", "REMOVE_DUPLICATES", "FILL_EMPTY", "REPLACE_VALUES", "SPLIT_COLUMN", "MERGE_COLUMNS", "APPEND_TABLES", "GROUP_AGGREGATE", "UNPIVOT_DATA", "TRANSPOSE_DATA")
OOXML_EXTENSIONS = {".xlsx", ".xlsm", ".xltx", ".xltm"}
STRUCTURE_REQUIRES_COM = {
    "has_vba", "has_activex", "has_ole_objects", "has_data_model", "has_power_query",
    "has_external_connections", "has_pivot_tables",
}
COM_SAFE_MUTATIONS = {"SET_VALUE", "SET_VALUES", "DELETE_ROWS", "INSERT_ROWS", "DELETE_COLUMNS", "INSERT_COLUMNS", "CLEAR_CONTENTS", "CLEAR_FORMATS"}


class EngineRouter:
    def decide(self, operation: OperationSpec, capability: CapabilityProfile, snapshot: WorkbookSnapshot | None = None) -> EngineDecision:
        required = set(operation.required_capabilities)
        if operation.engine_hint != EngineMode.AUTO:
            return self._explicit(operation.engine_hint, capability, required)

        if snapshot is not None:
            suffix = snapshot.source_path.suffix.lower()
            complex_workbook = any(bool(getattr(snapshot, name, False)) for name in STRUCTURE_REQUIRES_COM)
            if suffix in {".xls", ".xlsb", ".xlam", ".xltm"} or complex_workbook:
                if not capability.excel.installed:
                    return EngineDecision(supported=False, engine=None, reason="Operation requires Excel COM to preserve workbook fidelity, but Excel is not installed", required_capabilities=frozenset(required | {"excel_com"}), fidelity_risk="fail-closed")
                return EngineDecision(supported=True, engine=EngineMode.EXCEL_COM, reason="Workbook structure requires Excel COM", required_capabilities=frozenset(required | {"excel_com"}))
            if suffix in {".csv", ".txt"}:
                return EngineDecision(supported=True, engine=EngineMode.DATAFRAME, reason="Delimited text is handled by DataFrame engine", required_capabilities=frozenset(required))

        if operation.opcode.startswith(COM_PREFIXES):
            if not capability.excel.installed:
                return EngineDecision(supported=False, engine=None, reason="Operation requires Excel COM, but Excel is not installed", required_capabilities=frozenset(required | {"excel_com"}), fidelity_risk="fail-closed")
            return EngineDecision(supported=True, engine=EngineMode.EXCEL_COM, reason="Operation uses Excel COM", required_capabilities=frozenset(required | {"excel_com"}))
        if operation.opcode.startswith(DATAFRAME_PREFIXES):
            return EngineDecision(supported=True, engine=EngineMode.DATAFRAME, reason="Data operation planned through DataFrame with non-destructive writeback", required_capabilities=frozenset(required), fidelity_risk="writeback-required")
        return EngineDecision(supported=True, engine=EngineMode.HYBRID, reason="Hybrid engine will choose safest local implementation", required_capabilities=frozenset(required))

    def _explicit(self, engine: EngineMode, capability: CapabilityProfile, required: set[str]) -> EngineDecision:
        if engine == EngineMode.EXCEL_COM and not capability.excel.installed:
            return EngineDecision(supported=False, engine=None, reason="Operation requires Excel COM, but Excel is not installed", required_capabilities=frozenset(required | {"excel_com"}), fidelity_risk="COM capability unavailable")
        return EngineDecision(supported=True, engine=engine, reason="Explicit engine hint", required_capabilities=frozenset(required))

    def choose(self, operation: OperationSpec, capability: CapabilityProfile, snapshot: WorkbookSnapshot | None = None) -> EngineMode:
        decision = self.decide(operation, capability, snapshot)
        if not decision.supported or decision.engine is None:
            raise ValueError(decision.reason)
        return decision.engine
