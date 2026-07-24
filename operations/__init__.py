from .registry import OperationRegistry

def build_default_registry():
    from .builtin import build_default_registry as _build_default_registry
    return _build_default_registry()

__all__ = ["OperationRegistry", "build_default_registry"]
