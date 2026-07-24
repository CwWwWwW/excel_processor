from __future__ import annotations
from discovery.excel_detector import build_capability_profile
from .pages import PAGE_NAMES
def run_app() -> int:
    from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QMainWindow, QSplitter, QTextEdit, QWidget, QVBoxLayout
    app=QApplication([]); window=QMainWindow(); window.setWindowTitle("Excel Processor v1.0.0")
    splitter=QSplitter(); nav=QListWidget(); nav.addItems(PAGE_NAMES); detail=QTextEdit(); detail.setReadOnly(True); cap=build_capability_profile()
    detail.setPlainText("环境中心\n"+f"Excel 产品：{cap.excel.display_name}\nCOM 版本：{cap.excel.com_version or ''}\n构建号：{cap.excel.build or ''}\nEXCEL.EXE 版本：{cap.excel.file_version or ''}\nOffice 位数：{cap.excel.bitness or cap.excel.platform or ''}\n\n处理平台：混合高保真模式\n输出兼容基线：自动\n输出格式：保持源格式")
    splitter.addWidget(nav); splitter.addWidget(detail); box=QWidget(); layout=QVBoxLayout(box); layout.addWidget(QLabel("纯本地 Excel 批处理桌面程序")); layout.addWidget(splitter); window.setCentralWidget(box); window.resize(1000,700); window.show(); return app.exec()
