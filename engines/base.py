from __future__ import annotations
from typing import Protocol
from contracts.plan import ExecutionContext, OperationCommand
from contracts.result import OperationResult
class Engine(Protocol):
    name: str
    def execute(self, command: OperationCommand, context: ExecutionContext) -> OperationResult: ...
