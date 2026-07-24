from __future__ import annotations
from typing import Hashable, Iterable
def uniqueness_errors(values: Iterable[Hashable], field_name: str) -> tuple[str,...]:
    seen=set(); dup=set()
    for v in values:
        if v in seen: dup.add(v)
        seen.add(v)
    return (f"字段 {field_name} 存在重复值：{len(dup)}",) if dup else ()
