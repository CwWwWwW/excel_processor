from __future__ import annotations
from typing import Any
from contracts.operation import ConditionExpr
def evaluate_condition(condition: ConditionExpr | None, row: dict[str, Any]) -> bool:
    if condition is None: return True
    op=condition.operator.lower(); value=row.get(condition.field or "")
    if op=="and": return all(evaluate_condition(c,row) for c in condition.children)
    if op=="or": return any(evaluate_condition(c,row) for c in condition.children)
    if op=="not": return not any(evaluate_condition(c,row) for c in condition.children)
    if op=="eq": return value==condition.value
    if op=="ne": return value!=condition.value
    if op=="contains": return str(condition.value) in str(value)
    raise ValueError(f"不支持的条件操作符：{condition.operator}")
