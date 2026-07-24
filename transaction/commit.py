from __future__ import annotations
import os, shutil
from pathlib import Path
def atomic_commit(candidate: Path, final_path: Path) -> None:
    final_path.parent.mkdir(parents=True, exist_ok=True)
    if candidate.stat().st_size == 0: raise ValueError("候选输出文件为空")
    if candidate.resolve().drive.lower() == final_path.resolve().drive.lower(): os.replace(candidate, final_path); return
    temp=final_path.with_name(f".{final_path.name}.tmp"); shutil.copy2(candidate, temp)
    if temp.stat().st_size != candidate.stat().st_size: raise ValueError("跨磁盘提交校验失败")
    os.replace(temp, final_path)
