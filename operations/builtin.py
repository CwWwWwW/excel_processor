from __future__ import annotations
from dataclasses import dataclass
from contracts.capability import CapabilityProfile
from contracts.job import EngineMode
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
from engines.com import ExcelComEngine
from engines.dataframe import DataFrameEngine
from engines.hybrid import HybridEngine
from engines.openxml import OpenXmlEngine
from .registry import OperationRegistry
@dataclass(frozen=True)
class EngineBackedHandler:
    opcode: str; engine_mode: EngineMode; category: str="standard"; chinese_name: str="标准操作"
    def validate(self, command: OperationCommand, capability: CapabilityProfile) -> tuple[str,...]:
        if self.engine_mode == EngineMode.EXCEL_COM and not capability.excel.installed: return ("该操作需要 Excel COM，但当前未检测到 Excel",)
        if command.operation.opcode != self.opcode: return ("命令 opcode 与处理器不匹配",)
        return ()
    def estimate(self, command: OperationCommand) -> int: return 1
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult:
        engine={EngineMode.EXCEL_COM:ExcelComEngine(), EngineMode.OPENXML:OpenXmlEngine(), EngineMode.DATAFRAME:DataFrameEngine(), EngineMode.HYBRID:HybridEngine()}[self.engine_mode]
        return engine.execute(command, context)
    def verify(self, command: OperationCommand, result: OperationResult) -> tuple[str,...]: return tuple(result.errors)
def build_default_registry() -> OperationRegistry:
    r=OperationRegistry()
    for opcode,engine,name in (("SET_VALUE",EngineMode.HYBRID,"写入值"),("DELETE_ROWS",EngineMode.OPENXML,"删除行"),("SAVE_AS",EngineMode.EXCEL_COM,"另存为"),("DEDUP_DATA",EngineMode.DATAFRAME,"删除重复数据"),("COM_GET",EngineMode.EXCEL_COM,"读取 COM 属性"),("COM_SET",EngineMode.EXCEL_COM,"设置 COM 属性"),("COM_CALL",EngineMode.EXCEL_COM,"调用 COM 方法")):
        r.register(EngineBackedHandler(opcode, engine, chinese_name=name))
    return r
