from __future__ import annotations
from pathlib import Path
from discovery.file_scanner import sha256_file
OOXML_EXTS={'.xlsx','.xlsm','.xltx','.xltm','.xlam'}
def validate_file_basic(path: Path) -> tuple[dict[str,bool], tuple[str,...], tuple[str,...], str | None]:
    checks={'exists':path.exists(), 'non_zero':path.exists() and path.stat().st_size>0, 'extension_present':bool(path.suffix)}; errors=[n for n,ok in checks.items() if not ok]
    digest=sha256_file(path) if path.exists() and path.is_file() and path.stat().st_size>0 else None
    if path.exists() and path.suffix.lower() in OOXML_EXTS:
        try:
            with path.open('rb') as f: checks['zip_header']=f.read(4)==b'PK\x03\x04'
        except OSError: checks['zip_header']=False
        if not checks['zip_header']: errors.append('zip_header')
    return checks, (), tuple(errors), digest
