from __future__ import annotations
def compare_object_counts(before: dict[str,int], after: dict[str,int]) -> tuple[str,...]:
    return tuple(f"对象数量减少：{k} {v}->{after.get(k,0)}" for k,v in before.items() if after.get(k,0)<v)
