from __future__ import annotations
from contracts.operation import OperationSpec
def detect_conflicts(operations: tuple[OperationSpec,...]) -> tuple[str,...]:
    warnings=[]; structural_seen=False
    for op in operations:
        if op.opcode.startswith(("DELETE_","INSERT_","MOVE_","RENAME_")): structural_seen=True
        if structural_seen and op.opcode.startswith(("JOIN_","LOOKUP_","SET_FORMULA","VALIDATE_")) and not op.depends_on:
            warnings.append(f"操作 {op.opcode} 位于结构修改之后且未声明依赖，编译器保持显式顺序并提示复核")
    return tuple(warnings)
