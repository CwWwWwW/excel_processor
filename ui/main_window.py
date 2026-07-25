from __future__ import annotations
from discovery.excel_detector import build_capability_profile
from excel_processor.paths import ensure_runtime_root
from .qt_compat import QApplication, QLabel, QMainWindow, QMessageBox, QPushButton, QSplitter, QTextEdit, QVBoxLayout, QWidget, exec_app


def run_app() -> int:
    app = QApplication.instance() or QApplication([])
    cap = build_capability_profile()
    runtime = ensure_runtime_root()
    window = QMainWindow()
    window.setWindowTitle("Excel Processor")
    splitter = QSplitter()
    nav = QTextEdit()
    nav.setReadOnly(True)
    nav.setPlainText("Operation Registry\nJobs\nHistory\nDiagnostics")
    detail = QTextEdit()
    detail.setReadOnly(True)
    mode = "Full Excel COM mode" if cap.excel.installed else "Limited safe mode (Excel not detected)"
    detail.setPlainText(
        f"Status\n"
        f"Mode: {mode}\n"
        f"Excel: {cap.excel.display_name}\n"
        f"COM version: {cap.excel.com_version or ''}\n"
        f"Build: {cap.excel.build or ''}\n"
        f"EXCEL.EXE version: {cap.excel.file_version or ''}\n"
        f"Office bitness: {cap.excel.bitness or cap.excel.platform or ''}\n"
        f"Runtime data: {runtime}\n\n"
        "Source files are never modified directly.\n"
        "COM work is isolated in the Excel worker process.\n"
    )
    open_logs = QPushButton("Open log location")
    open_logs.clicked.connect(lambda: QMessageBox.information(window, "Log location", str(runtime / "logs")))
    splitter.addWidget(nav)
    splitter.addWidget(detail)
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.addWidget(QLabel("Excel Processor desktop application"))
    layout.addWidget(open_logs)
    layout.addWidget(splitter)
    window.setCentralWidget(box)
    window.resize(1000, 700)
    window.show()
    return exec_app(app)
