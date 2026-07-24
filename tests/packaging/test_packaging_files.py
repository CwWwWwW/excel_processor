from pathlib import Path

def test_packaging_assets_exist():
    for p in ['installer/ExcelProcessor.iss','build/excel_processor.spec','resources/operation_catalog.json','requirements/modern-x64.lock']:
        assert Path(p).exists()

def test_pyinstaller_uses_onedir_no_upx():
    spec=Path('build/excel_processor.spec').read_text(encoding='utf-8')
    assert 'COLLECT(' in spec
    assert 'upx=False' in spec


def test_pyproject_has_no_unbounded_runtime_dependencies():
    text = Path('pyproject.toml').read_text(encoding='utf-8')
    assert 'pydantic>=' not in text
    assert 'PySide6>=' not in text
    assert 'pandas>=' not in text


def test_locks_have_hashes():
    for lock in Path('requirements').glob('*.lock'):
        content = lock.read_text(encoding='utf-8').strip().splitlines()
        assert content
        assert all('--hash=sha256:' in line for line in content)
