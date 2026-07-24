from __future__ import annotations
from contracts.capability import CapabilityProfile, EngineDecision
from contracts.job import EngineMode
from contracts.operation import OperationSpec
COM_PREFIXES=("PIVOT_","CHART_","VBA_","CONNECTION_","POWER_QUERY_","PRINT_","COM_","SAVE_AS")
DATAFRAME_PREFIXES=("JOIN_","GROUP_","FILTER_DATA_","PIVOT_DATA_","DEDUP_","CLEAN_TEXT")
OOXML_EXTENSIONS={'.xlsx','.xlsm','.xltx','.xltm'}
class EngineRouter:
    def decide(self, operation: OperationSpec, capability: CapabilityProfile) -> EngineDecision:
        required=set(operation.required_capabilities)
        if operation.engine_hint != EngineMode.AUTO:
            if operation.engine_hint == EngineMode.EXCEL_COM and not capability.excel.installed:
                return EngineDecision(supported=False, engine=None, reason='?????? Excel COM?????? Excel', required_capabilities=frozenset(required|{'excel_com'}), fidelity_risk='COM capability unavailable')
            return EngineDecision(supported=True, engine=operation.engine_hint, reason='????????', required_capabilities=frozenset(required))
        if operation.opcode.startswith(COM_PREFIXES):
            if not capability.excel.installed:
                return EngineDecision(supported=False, engine=None, reason='????? Excel COM???? Excel ????????????', required_capabilities=frozenset(required|{'excel_com'}), fidelity_risk='fail-closed')
            return EngineDecision(supported=True, engine=EngineMode.EXCEL_COM, reason='???????????? Excel COM', required_capabilities=frozenset(required|{'excel_com'}))
        if operation.opcode.startswith(DATAFRAME_PREFIXES):
            return EngineDecision(supported=True, engine=EngineMode.DATAFRAME, reason='???????? DataFrame???????????', required_capabilities=frozenset(required), fidelity_risk='writeback-required')
        return EngineDecision(supported=True, engine=EngineMode.HYBRID, reason='?????????', required_capabilities=frozenset(required))
    def choose(self, operation: OperationSpec, capability: CapabilityProfile) -> EngineMode:
        decision = self.decide(operation, capability)
        if not decision.supported or decision.engine is None:
            raise ValueError(decision.reason)
        return decision.engine
