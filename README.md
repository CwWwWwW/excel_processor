# Excel Processor v1.0.0

A local Windows desktop Excel processing framework built around PySide6, Python 3.11, Microsoft Excel COM automation, openpyxl, pandas, and SQLite.

The application never modifies source files directly. Jobs are prepared in a runtime workspace, written to candidate artifacts, validated, and only then atomically committed to the selected output directory.

## Quick checks

```powershell
python -m pytest
python -m app.main --self-check
```

Target remote: `https://github.com/CwWwWwW/excel_processor.git`.
