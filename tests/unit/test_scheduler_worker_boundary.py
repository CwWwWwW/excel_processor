from pathlib import Path


def test_scheduler_never_instantiates_excel_com_directly():
    text = Path("scheduler/job_scheduler.py").read_text(encoding="utf-8")
    assert "ExcelComEngine" not in text
    assert "engines.com" not in text
    assert "ExcelWorkerPool" in text
