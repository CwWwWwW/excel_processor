from __future__ import annotations
from uuid import UUID
from contracts.operation import OperationSpec
def topological_sort(operations: tuple[OperationSpec,...]) -> tuple[OperationSpec,...]:
    by_id={op.operation_id:op for op in operations if op.enabled}; incoming: dict[UUID,set[UUID]]={i:set(op.depends_on)&set(by_id) for i,op in by_id.items()}; ready=[i for i,d in incoming.items() if not d]; result=[]
    while ready:
        op_id=ready.pop(0); result.append(by_id[op_id])
        for other,deps in incoming.items():
            if op_id in deps:
                deps.remove(op_id)
                if not deps and by_id[other] not in result and other not in ready: ready.append(other)
    if len(result)!=len(by_id): raise ValueError("执行计划存在循环依赖")
    return tuple(result)
