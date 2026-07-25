from __future__ import annotations

import hashlib
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    root = Path.cwd()
    checksum_file = root / "SHA256SUMS.txt"
    if not checksum_file.exists():
        raise SystemExit("Missing SHA256SUMS.txt")
    for line in checksum_file.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        expected, rel = line.split(None, 1)
        rel = rel.strip()
        path = root / rel
        if not path.exists():
            raise SystemExit(f"Missing checksummed file: {rel}")
        actual = sha256(path)
        if actual.lower() != expected.lower():
            raise SystemExit(f"SHA-256 mismatch for {rel}: {actual} != {expected}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
