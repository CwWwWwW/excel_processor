from __future__ import annotations
from discovery.excel_detector import build_capability_profile
from excel_processor.paths import ensure_runtime_root
from excel_processor.version import __version__
from .pages import PAGE_NAMES
from .qt_compat import QApplication, QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton, QSplitter, QTextEdit, QWidget, QVBoxLayout, enable_dpi_awareness, exec_app

def run_app() -> int:
    enable_dpi_awareness(); app=QApplication([]); window=QMainWindow(); window.setWindowTitle(f'Excel Processor v{__version__}')
    splitter=QSplitter(); nav=QListWidget(); nav.addItems(PAGE_NAMES); detail=QTextEdit(); detail.setReadOnly(True); cap=build_capability_profile(); runtime=ensure_runtime_root()
    detail.setPlainText(f"????\nExcel ???{cap.excel.display_name}\nCOM ???{cap.excel.com_version or ''}\n????{cap.excel.build or ''}\nEXCEL.EXE ???{cap.excel.file_version or ''}\nOffice ???{cap.excel.bitness or cap.excel.platform or ''}\n?????{runtime}\n\n????????????\n?????????\n??????????")
    open_logs=QPushButton('??????'); open_logs.clicked.connect(lambda: QMessageBox.information(window, '????', str(runtime/'logs')))
    splitter.addWidget(nav); splitter.addWidget(detail); box=QWidget(); layout=QVBoxLayout(box); layout.addWidget(QLabel('??? Excel ???????')); layout.addWidget(open_logs); layout.addWidget(splitter); window.setCentralWidget(box); window.resize(1000,700); window.show(); return exec_app(app)
