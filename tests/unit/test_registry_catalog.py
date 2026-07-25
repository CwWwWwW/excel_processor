import json
from pathlib import Path

from operations import build_default_registry
from scripts.generate_operation_catalog import build_catalog


def test_registry_contains_required_core_operations():
    registry = build_default_registry()
    required = {"OPEN_WORKBOOK", "SAVE_WORKBOOK", "SAVE_AS", "EXPORT_PDF", "SET_VALUE", "DELETE_ROWS", "CREATE_PIVOT_TABLE", "ADD_HYPERLINK"}
    assert required.issubset(set(registry.list_opcodes()))
    assert len(registry.list_opcodes()) >= 100


def test_catalog_matches_registry():
    expected = build_catalog()
    actual = json.loads(Path("resources/operation_catalog.json").read_text(encoding="utf-8"))
    assert actual == expected
