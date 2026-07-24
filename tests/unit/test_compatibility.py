from discovery.typelib_scanner import enumerate_file_formats
from validation.compatibility_validator import conversion_loss_warnings

def test_vba_xlsx_warning():
    xlsx = next(fmt for fmt in enumerate_file_formats() if fmt.file_format == 51)
    warnings = conversion_loss_warnings(True, 2, xlsx)
    assert any('VBA' in warning for warning in warnings)
