from __future__ import annotations
try:
    import pythoncom  # noqa: F401
    import pywintypes  # noqa: F401
except Exception as exc:
    raise RuntimeError(f"pywin32 runtime initialization failed: {exc}")
