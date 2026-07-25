from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    path = Path("SBOM.spdx.json")
    if not path.exists():
        raise SystemExit("Missing SBOM.spdx.json")
    text = path.read_text(encoding="utf-8-sig")
    lowered = text.lower()
    if "stand-in" in lowered or "sample" in lowered:
        raise SystemExit("SBOM contains stand-in markers")
    doc = json.loads(text)
    if doc.get("spdxVersion") != "SPDX-2.3":
        raise SystemExit("SBOM is not SPDX-2.3")
    packages = doc.get("packages") or []
    names = {str(pkg.get("name", "")).lower() for pkg in packages if isinstance(pkg, dict)}
    required = {"pydantic", "openpyxl"}
    missing = required - names
    if missing:
        raise SystemExit(f"SBOM missing required packages: {sorted(missing)}")
    files = doc.get("files") or []
    if not files:
        raise SystemExit("SBOM does not describe artifact files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
