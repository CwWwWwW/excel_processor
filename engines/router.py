from __future__ import annotations
from contracts.capability import CapabilityProfile
from contracts.job import EngineMode
from contracts.operation import OperationSpec
class EngineRouter:
    def choose(self, operation: OperationSpec, capability: CapabilityProfile) -> EngineMode:
        if operation.engine_hint != EngineMode.AUTO: return operation.engine_hint
        if operation.opcode.startswith(("PIVOT_","CHART_","VBA_","CONNECTION_","POWER_QUERY_","PRINT_","COM_","SAVE_AS")):
            return EngineMode.EXCEL_COM if capability.excel.installed else EngineMode.HYBRID
        if operation.opcode.startswith(("JOIN_","GROUP_","FILTER_DATA_","PIVOT_DATA_","DEDUP_","CLEAN_TEXT")): return EngineMode.DATAFRAME
        return EngineMode.HYBRID
