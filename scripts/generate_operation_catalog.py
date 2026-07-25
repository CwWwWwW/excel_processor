from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from operations import build_default_registry


def build_catalog() -> list[dict]:
    registry = build_default_registry()
    rows = []
    for row in registry.catalog():
        rows.append(
            {
                "opcode": row["opcode"],
                "handler_class": row["handler_class"],
                "implemented": bool(row.get("implemented", False)),
                "parameter_schema": row.get("parameter_schema", {}),
                "supported_engines": list(row.get("supported_engines", ())),
                "supported_file_formats": list(row.get("supported_file_formats", ())),
                "minimum_excel_version": row.get("minimum_excel_version"),
                "required_com_members": list(row.get("required_com_members", ())),
                "requires_excel": bool(row.get("requires_excel", False)),
                "preserves_vba": bool(row.get("preserves_vba", True)),
                "supports_skip_row": bool(row.get("supports_skip_row", False)),
                "validators": list(row.get("validators", ())),
                "tests": list(row.get("tests", ())),
                "category": row.get("category", "general"),
                "chinese_name": row.get("chinese_name", ""),
            }
        )
    return rows


def main() -> int:
    target = Path("resources/operation_catalog.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_catalog(), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
