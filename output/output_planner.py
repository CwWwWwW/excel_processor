from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict

from contracts.capability import CapabilityProfile
from contracts.job import OutputSpec
from discovery.workbook_inspector import WorkbookSnapshot


_SAVE_AS_FORMATS: dict[int, tuple[str, str, bool]] = {
    51: (".xlsx", "save_as", False),  # xlOpenXMLWorkbook
    52: (".xlsm", "save_as", True),   # xlOpenXMLWorkbookMacroEnabled
    50: (".xlsb", "save_as", True),   # xlExcel12
    56: (".xls", "save_as", True),    # xlExcel8
    54: (".xltx", "save_as", False),
    53: (".xltm", "save_as", True),
    55: (".xlam", "save_as", True),
    6: (".csv", "data_export", False),
    62: (".csv", "data_export", False),  # xlCSVUTF8
    -4158: (".txt", "data_export", False),  # xlText
    42: (".txt", "data_export", False),  # xlUnicodeText
}

_FIXED_FORMATS: dict[int, tuple[str, str]] = {
    0: (".pdf", "export_fixed_format"),
    1: (".xps", "export_fixed_format"),
}


class OutputConversionPlan(BaseModel):
    model_config = ConfigDict(frozen=True)
    source_extension: str
    target_extension: str
    excel_file_format: int | None = None
    export_mode: str
    requires_excel: bool
    preserves_vba: bool
    preserves_workbook_objects: bool
    expected_losses: tuple[str, ...] = ()


def target_suffix_for_format(format_code: int | None, source_suffix: str) -> str:
    if format_code is None:
        return source_suffix
    if format_code in _FIXED_FORMATS:
        return _FIXED_FORMATS[format_code][0]
    if format_code in _SAVE_AS_FORMATS:
        return _SAVE_AS_FORMATS[format_code][0]
    raise ValueError(f"Unsupported Excel output format_code: {format_code}")


def _losses(snapshot: WorkbookSnapshot, target_extension: str) -> tuple[str, ...]:
    losses: list[str] = []
    if target_extension in {".csv", ".txt"}:
        losses.extend([
            "formulas are exported as displayed values",
            "cell formatting is lost",
            "only the selected worksheet is exported",
            "charts are lost",
            "data validation is lost",
            "conditional formatting is lost",
            "defined names are lost",
        ])
    if snapshot.has_vba and target_extension in {".xlsx", ".xltx", ".csv", ".txt", ".pdf", ".xps"}:
        losses.append("VBA project cannot be preserved in target format")
    if getattr(snapshot, "has_charts", False) and target_extension in {".csv", ".txt"}:
        losses.append("chart objects are lost")
    if getattr(snapshot, "has_pivot_tables", False) and target_extension in {".csv", ".txt"}:
        losses.append("pivot table objects are lost")
    return tuple(dict.fromkeys(losses))


def plan_output_conversion(
    snapshot: WorkbookSnapshot,
    output: OutputSpec,
    capability: CapabilityProfile,
    compatibility_baseline: str | None = None,
) -> OutputConversionPlan:
    source_extension = Path(snapshot.source_path).suffix.lower()
    if output.preserve_source_format or output.format_code is None:
        return OutputConversionPlan(
            source_extension=source_extension,
            target_extension=source_extension,
            export_mode="copy_working_to_candidate",
            requires_excel=source_extension not in {".xlsx", ".xlsm", ".xltx", ".xltm", ".csv", ".txt"},
            preserves_vba=bool(snapshot.has_vba),
            preserves_workbook_objects=True,
        )

    target_extension = target_suffix_for_format(output.format_code, source_extension)
    if output.format_code in _FIXED_FORMATS:
        mode = "export_fixed_format"
        excel_format = None
        requires_excel = True
        preserves_vba = False
        preserves_objects = target_extension in {".pdf", ".xps"}
    else:
        _, mode, preserves_vba = _SAVE_AS_FORMATS[output.format_code]
        excel_format = output.format_code if mode == "save_as" else None
        requires_excel = mode in {"save_as", "data_export"}
        preserves_objects = mode == "save_as"

    losses = _losses(snapshot, target_extension)
    if snapshot.has_vba and not preserves_vba and target_extension in {".xlsx", ".xltx"}:
        raise ValueError("Unsafe conversion would remove VBA; choose a macro-enabled target or explicitly allow a lossy export")
    if requires_excel and not capability.excel.installed:
        raise ValueError(f"Conversion to {target_extension} requires Excel COM, but Excel is not installed")

    return OutputConversionPlan(
        source_extension=source_extension,
        target_extension=target_extension,
        excel_file_format=excel_format,
        export_mode=mode,
        requires_excel=requires_excel,
        preserves_vba=preserves_vba or not snapshot.has_vba,
        preserves_workbook_objects=preserves_objects,
        expected_losses=losses,
    )
