import os
from excel_processor.paths import runtime_root

def test_runtime_uses_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv('LOCALAPPDATA', str(tmp_path))
    monkeypatch.delenv('EXCEL_PROCESSOR_RUNTIME', raising=False)
    monkeypatch.delenv('EXCEL_PROCESSOR_PORTABLE', raising=False)
    assert runtime_root() == tmp_path / 'ExcelProcessor'
