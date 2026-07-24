from __future__ import annotations
from typing import Any
from contracts.operation import OperationSpec
_BLOCKED_MEMBERS={'Run','ExecuteExcel4Macro'}
def _assert_safe_member(member: str, allowed_members: set[str] | None=None) -> None:
    if member.startswith('_') or member in _BLOCKED_MEMBERS: raise ValueError(f'???????? COM ???{member}')
    if allowed_members is not None and allowed_members and member not in allowed_members: raise ValueError(f'COM ????????????{member}')
def _resolve_chain(root: Any, chain: tuple[dict[str, Any], ...], allowed_members: set[str] | None=None) -> Any:
    current=root
    for item in chain:
        member=str(item.get('member',''))
        if not member: raise ValueError('COM object_chain ?? member')
        _assert_safe_member(member, allowed_members)
        if not hasattr(current, member): raise ValueError(f'COM ????????{member}')
        current=getattr(current, member)
        if 'item' in item: current=current.Item(item['item'])
        args=item.get('arguments')
        if args is not None:
            if not callable(current): raise ValueError(f'COM ???????{member}')
            current=current(*args)
    return current
def execute_generic_com(workbook: Any, operation: OperationSpec, allowed_members: set[str] | None=None) -> Any:
    if operation.parameters.get('advanced_com_enabled') is False: raise ValueError('?? COM ????????')
    target=_resolve_chain(workbook, operation.target.object_chain, allowed_members); member=str(operation.parameters.get('member',''))
    if not member: raise ValueError('?? COM ???? parameters.member')
    _assert_safe_member(member, allowed_members)
    if not hasattr(target, member): raise ValueError(f'COM ????????{member}')
    if operation.opcode=='COM_GET': return getattr(target, member)
    if operation.opcode=='COM_SET':
        if 'value' not in operation.parameters: raise ValueError('COM_SET ?? parameters.value')
        setattr(target, member, operation.parameters.get('value')); return None
    if operation.opcode=='COM_CALL':
        fn=getattr(target, member)
        if not callable(fn): raise ValueError(f'COM ???????{member}')
        return fn(*(operation.parameters.get('arguments') or []))
    raise ValueError(f'?????? COM opcode?{operation.opcode}')
