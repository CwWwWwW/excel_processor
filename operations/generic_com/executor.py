from __future__ import annotations
from typing import Any
from contracts.operation import OperationSpec
_BLOCKED_MEMBERS = {"Run"}
def _assert_safe_member(member: str) -> None:
    if member.startswith("_") or member in _BLOCKED_MEMBERS: raise ValueError(f"安全策略禁止访问 COM 成员：{member}")
def _resolve_chain(root: Any, chain: tuple[dict[str, Any], ...]) -> Any:
    current=root
    for item in chain:
        member=str(item.get("member", ""))
        if not member: raise ValueError("COM object_chain 缺少 member")
        _assert_safe_member(member)
        if not hasattr(current, member): raise ValueError(f"COM 对象不存在成员：{member}")
        current=getattr(current, member)
        if "item" in item: current=current.Item(item["item"])
        args=item.get("arguments")
        if args is not None:
            if not callable(current): raise ValueError(f"COM 成员不是方法：{member}")
            current=current(*args)
    return current
def execute_generic_com(workbook: Any, operation: OperationSpec) -> Any:
    target=_resolve_chain(workbook, operation.target.object_chain); member=str(operation.parameters.get("member", ""))
    if not member: raise ValueError("通用 COM 操作缺少 parameters.member")
    _assert_safe_member(member)
    if not hasattr(target, member): raise ValueError(f"COM 对象不存在成员：{member}")
    if operation.opcode=="COM_GET": return getattr(target, member)
    if operation.opcode=="COM_SET":
        if "value" not in operation.parameters: raise ValueError("COM_SET 缺少 parameters.value")
        setattr(target, member, operation.parameters.get("value")); return None
    if operation.opcode=="COM_CALL":
        fn=getattr(target, member)
        if not callable(fn): raise ValueError(f"COM 成员不是方法：{member}")
        return fn(*(operation.parameters.get("arguments") or []))
    raise ValueError(f"不支持的通用 COM opcode：{operation.opcode}")
