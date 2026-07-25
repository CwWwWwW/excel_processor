from pathlib import Path


TEXT_SUFFIXES = {".py", ".json", ".md", ".toml", ".iss", ".ps1", ".spec", ".yaml", ".yml"}
SKIP_PARTS = {".git", ".pytest_cache", "__pycache__"}


def test_source_files_are_utf8_without_corruption_markers():
    offenders = []
    for path in Path(".").rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if "\ufffd" in text or ("?" * 4) in text:
            offenders.append(str(path))
    assert offenders == []
