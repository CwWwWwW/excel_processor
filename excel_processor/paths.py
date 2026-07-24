from __future__ import annotations

import os
import sys
from pathlib import Path

from .version import APP_NAME


def is_portable_mode() -> bool:
    if os.environ.get("EXCEL_PROCESSOR_PORTABLE", "").lower() in {"1", "true", "yes"}:
        return True
    base = Path(getattr(sys, "_MEIPASS", Path(sys.argv[0]).resolve().parent))
    return (base / "portable.flag").exists()


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def runtime_root() -> Path:
    override = os.environ.get("EXCEL_PROCESSOR_RUNTIME")
    if override:
        return Path(override).expanduser().resolve()
    if is_portable_mode():
        return application_dir() / "portable_data"
    local = os.environ.get("LOCALAPPDATA")
    if local:
        return Path(local) / APP_NAME
    return Path.home() / "AppData" / "Local" / APP_NAME


def ensure_runtime_root() -> Path:
    root = runtime_root()
    for child in ("database", "logs", "jobs", "crash_reports", "diagnostics", "crash_recovery"):
        (root / child).mkdir(parents=True, exist_ok=True)
    return root


def legacy_runtime_root(project_root: Path | None = None) -> Path:
    return (project_root or Path.cwd()) / "runtime"
