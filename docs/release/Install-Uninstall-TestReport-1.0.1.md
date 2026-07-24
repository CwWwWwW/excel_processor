# Install and Uninstall Test Report - 1.0.1

## Automated checks in current environment
- `python -m pytest`: passed.
- `python -m app.main --self-check`: passed in no-Excel limited mode.
- Packaging scripts are present and smoke-test entry is defined.

## Manual VM checks required
Run `scripts/vm_acceptance_matrix.ps1` after installing the offline payload on each supported Windows/Excel matrix entry. Verify uninstall keeps user outputs, backups and `%LOCALAPPDATA%\ExcelProcessor` data unless the user explicitly removes data.
