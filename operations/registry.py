from __future__ import annotations
from typing import Protocol
from contracts.capability import CapabilityProfile
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
class OperationHandler(Protocol):
    opcode: str
    def validate(self, command: OperationCommand, capability: CapabilityProfile) -> tuple[str, ...]: ...
    def estimate(self, command: OperationCommand) -> int: ...
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult: ...
    def verify(self, command: OperationCommand, result: OperationResult) -> tuple[str, ...]: ...
class OperationRegistry:
    def __init__(self) -> None: self._handlers: dict[str, OperationHandler] = {}
    def register(self, handler: OperationHandler) -> None:
        if handler.opcode in self._handlers: raise ValueError(f"重复操作编号：{handler.opcode}")
        self._handlers[handler.opcode]=handler
    def get(self, opcode: str) -> OperationHandler:
        try: return self._handlers[opcode]
        except KeyError as exc: raise ValueError(f"未注册操作：{opcode}") from exc
    def list_opcodes(self) -> tuple[str, ...]: return tuple(sorted(self._handlers))
