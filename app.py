from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication, QIcon
from PySide6.QtWidgets import QApplication, QProgressDialog

from core.db import init_db
from ui.main_window import MainWindow


def build_dark_stylesheet() -> str:
    return """
    QWidget {
        background-color: #1e1f22;
        color: #e8e8e8;
        font-size: 10pt;
    }

    QMainWindow, QDialog {
        background-color: #1e1f22;
    }

    QLabel {
        color: #e8e8e8;
        background: transparent;
    }

    QLineEdit, QTextEdit, QTextBrowser, QPlainTextEdit, QComboBox, QSpinBox, QListWidget, QTableWidget {
        background-color: #2a2d31;
        color: #f0f0f0;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 4px;
        selection-background-color: #3d6ea8;
        selection-color: white;
    }

    QPushButton {
        background-color: #2f3136;
        color: #f0f0f0;
        border: 1px solid #555;
        border-radius: 5px;
        padding: 6px 10px;
    }

    QPushButton:hover {
        background-color: #3a3d42;
    }

    QPushButton:pressed {
        background-color: #25282c;
    }

    QCheckBox, QRadioButton {
        color: #e8e8e8;
        background: transparent;
    }

    QMenuBar {
        background-color: #232529;
        color: #f0f0f0;
    }

    QMenuBar::item:selected {
        background-color: #3a3d42;
    }

    QMenu {
        background-color: #232529;
        color: #f0f0f0;
        border: 1px solid #444;
    }

    QMenu::item:selected {
        background-color: #3a3d42;
    }

    QHeaderView::section {
        background-color: #2f3136;
        color: #f0f0f0;
        border: 1px solid #444;
        padding: 4px;
    }

    QGroupBox {
        border: 1px solid #444;
        border-radius: 6px;
        margin-top: 10px;
        padding-top: 8px;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: #f0f0f0;
    }

    QScrollArea {
        border: none;
        background: transparent;
    }

    QTableWidget {
        gridline-color: #444;
    }

    QProgressDialog {
        background-color: #1e1f22;
        color: #f0f0f0;
    }
    """


def main() -> int:
    QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(build_dark_stylesheet())

    icon_path = Path(__file__).resolve().parent / "assets" / "icons" / "project_vault_icon_128.ico"
    app_icon = QIcon(str(icon_path)) if icon_path.exists() else QIcon()
    app.setWindowIcon(app_icon)

    # ── Startup loading dialog ───────────────────────────────────────
    loading = QProgressDialog("Starting Project Vault...", None, 0, 0)
    loading.setWindowTitle("Loading")
    loading.setWindowModality(Qt.NonModal)
    loading.setMinimumDuration(0)
    loading.setAutoClose(False)
    loading.setAutoReset(False)
    loading.setCancelButton(None)
    loading.setWindowIcon(app_icon)
    loading.setValue(0)
    loading.show()
    QApplication.processEvents()

    loading.setLabelText("Initializing database...")
    QApplication.processEvents()
    init_db()

    loading.setLabelText("Building main window...")
    QApplication.processEvents()
    window = MainWindow()
    window.setWindowIcon(app_icon)

    loading.setLabelText("Loading projects and UI data...")
    QApplication.processEvents()
    window._finish_startup(loading)

    loading.close()
    window.show()

    return app.exec()
