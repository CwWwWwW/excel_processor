from __future__ import annotations
from contracts.capability import FileFormatCapability
def conversion_loss_warnings(has_vba: bool, sheet_count: int, target_format: FileFormatCapability) -> tuple[str,...]:
    warnings=[]
    if has_vba and not target_format.can_preserve_vba: warnings.append("源文件含 VBA，目标格式不能保留宏工程")
    if target_format.category in {"data","fixed"}: warnings.append("目标格式可能丢失公式、图表、数据透视表、VBA、连接和格式")
    if sheet_count>1 and target_format.extension.lower() in {".csv",".txt"}: warnings.append("文本类格式只能导出指定工作表的数据")
    return tuple(warnings)
