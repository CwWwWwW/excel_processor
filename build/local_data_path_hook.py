from __future__ import annotations
import os
from pathlib import Path
if Path.cwd().joinpath("portable.flag").exists():
    os.environ.setdefault("EXCEL_PROCESSOR_PORTABLE", "1")
