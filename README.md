# Excel Processor v1.0.1

Pure local Windows Excel processing application framework with transactional output, Excel COM fidelity, OpenXML/CSV limited mode, SQLite persistence, and offline packaging scripts.

## Quick checks

```powershell
python -m pytest
python -m app.main --self-check
```

Runtime data is written to `%LOCALAPPDATA%\ExcelProcessor\` by default, or `portable_data/` in portable mode. Source Excel files are never modified directly.
