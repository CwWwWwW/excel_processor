from pathlib import Path
from uuid import uuid4

import pytest

from contracts.capability import CapabilityProfile, ExcelInstallation
from contracts.job import OutputSpec
from discovery.workbook_inspector import WorkbookSnapshot
from output.output_planner import plan_output_conversion, target_suffix_for_format


def _snapshot(path: str, **flags):
    return WorkbookSnapshot(file_id=uuid4(), source_path=Path(path), sha256="0" * 64, **flags)


def test_output_extension_mapping():
    assert target_suffix_for_format(51, ".xlsm") == ".xlsx"
    assert target_suffix_for_format(52, ".xlsx") == ".xlsm"
    assert target_suffix_for_format(50, ".xlsx") == ".xlsb"
    assert target_suffix_for_format(0, ".xlsx") == ".pdf"
    assert target_suffix_for_format(1, ".xlsx") == ".xps"


def test_xlsm_to_xlsx_macro_blocked():
    with pytest.raises(ValueError, match="VBA"):
        plan_output_conversion(
            _snapshot("book.xlsm", has_vba=True),
            OutputSpec(output_directory=Path("out"), preserve_source_format=False, format_code=51),
            CapabilityProfile(excel=ExcelInstallation(installed=True)),
        )


def test_pdf_uses_export_fixed_format():
    plan = plan_output_conversion(
        _snapshot("book.xlsx"),
        OutputSpec(output_directory=Path("out"), preserve_source_format=False, format_code=0),
        CapabilityProfile(excel=ExcelInstallation(installed=True)),
    )
    assert plan.export_mode == "export_fixed_format"
    assert plan.target_extension == ".pdf"
    assert plan.excel_file_format is None


def test_csv_format_loss_report():
    plan = plan_output_conversion(
        _snapshot("book.xlsx", has_charts=True),
        OutputSpec(output_directory=Path("out"), preserve_source_format=False, format_code=62),
        CapabilityProfile(excel=ExcelInstallation(installed=True)),
    )
    assert plan.export_mode == "data_export"
    assert "cell formatting is lost" in plan.expected_losses
