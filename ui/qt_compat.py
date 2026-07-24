from __future__ import annotations
try:
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QApplication, QFileDialog, QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton, QSplitter, QTextEdit, QWidget, QVBoxLayout
    QT_API='PySide6'
    def exec_app(app: QApplication) -> int: return app.exec()
except ImportError:
    from PySide2.QtCore import Qt, Signal
    from PySide2.QtWidgets import QAction, QApplication, QFileDialog, QLabel, QListWidget, QMainWindow, QMessageBox, QPushButton, QSplitter, QTextEdit, QWidget, QVBoxLayout
    QT_API='PySide2'
    def exec_app(app: QApplication) -> int: return app.exec_()
def enable_dpi_awareness() -> None:
    try:
        if QT_API == 'PySide6': QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        else: QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    except Exception as exc:
        _ = exc
