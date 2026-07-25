from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def detect_excel() -> dict:
    try:
        from discovery.excel_detector import detect_excel

        excel = detect_excel()
        return excel.model_dump(mode="json")
    except Exception as exc:
        return {"installed": False, "error": str(exc)}


def collect() -> dict:
    excel = detect_excel()
    return {
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "windows_version": platform.platform(),
        "windows_build": platform.version(),
        "system_bitness": platform.machine(),
        "python": sys.version,
        "excel": excel,
        "tests": {
            "open_workbook": "not_run" if not excel.get("installed") else "pending",
            "set_value": "not_run" if not excel.get("installed") else "pending",
            "delete_rows": "not_run" if not excel.get("installed") else "pending",
            "formula": "not_run" if not excel.get("installed") else "pending",
            "save": "not_run" if not excel.get("installed") else "pending",
            "save_as": "not_run" if not excel.get("installed") else "pending",
            "pdf": "not_run" if not excel.get("installed") else "pending",
            "xlsm_vba_preserved": "not_run" if not excel.get("installed") else "pending",
            "xlsb": "not_run" if not excel.get("installed") else "pending",
            "reopen_validation": "not_run" if not excel.get("installed") else "pending",
            "excel_process_residue": "not_run" if not excel.get("installed") else "pending",
        },
        "result": "limited_no_excel" if not excel.get("installed") else "requires_excel_suite_execution",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=None)
    parser.add_argument("--collect-environment", action="store_true")
    args = parser.parse_args()
    result = collect()
    if args.collect_environment or not args.output:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
