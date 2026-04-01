from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.models import Project, ScanCandidate
from core.scanner import discover_projects
from core.utils import normalize_tags


class ImportProjectsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Scan Parent Folder")
        self.resize(920, 560)

        self.projects_to_import: list[Project] = []
        self.candidates: list[ScanCandidate] = []
        self._busy_dialog: QProgressDialog | None = None

        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Choose a parent folder to scan for code projects...")

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)

        self.depth_spin = QSpinBox()
        self.depth_spin.setRange(1, 20)
        self.depth_spin.setValue(4)
        self.depth_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        self.depth_spin.setMinimumHeight(30)
        self.depth_spin.setMinimumWidth(90)
        self.depth_spin.setStyleSheet("""
            QSpinBox {
                padding-right: 28px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                width: 22px;
            }
        """)
        self.depth_spin.setToolTip("Maximum folder depth to scan below the selected parent folder.")

        scan_btn = QPushButton("Scan")
        scan_btn.clicked.connect(self.scan)

        top.addWidget(QLabel("Folder:"))
        top.addWidget(self.path_edit, 1)
        top.addWidget(browse_btn)
        top.addWidget(QLabel("Depth:"))
        top.addWidget(self.depth_spin)
        top.addWidget(scan_btn)
        layout.addLayout(top)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Import", "Name", "Language", "Framework", "Git", "Path"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        helper = QLabel(
            "The scanner looks for common project markers such as package.json, "
            "pyproject.toml, CMakeLists.txt, build.gradle, .git, README.md, and source files. "
            "Increase Depth to search farther below the selected parent folder."
        )
        helper.setWordWrap(True)
        layout.addWidget(helper)

        buttons = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self._set_all_checks(True))

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._set_all_checks(False))

        import_btn = QPushButton("Import Selected")
        import_btn.clicked.connect(self.accept_selection)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(select_all_btn)
        buttons.addWidget(clear_btn)
        buttons.addStretch(1)
        buttons.addWidget(import_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        # Only auto-run after the dialog paints, and only if a folder is already set.
        QTimer.singleShot(0, self._run_initial_scan)

    def _show_busy_dialog(self, message: str = "Scanning parent folder...\n\nPlease wait...") -> None:
        self._close_busy_dialog()
        self._busy_dialog = QProgressDialog(message, None, 0, 0, self)
        self._busy_dialog.setWindowTitle("Scanning")
        self._busy_dialog.setWindowModality(Qt.WindowModal)
        self._busy_dialog.setMinimumDuration(0)
        self._busy_dialog.setAutoClose(False)
        self._busy_dialog.setAutoReset(False)
        self._busy_dialog.setCancelButton(None)
        self._busy_dialog.setValue(0)
        self._busy_dialog.show()
        QApplication.processEvents()

    def _close_busy_dialog(self) -> None:
        if self._busy_dialog is not None:
            self._busy_dialog.close()
            self._busy_dialog.deleteLater()
            self._busy_dialog = None
            QApplication.processEvents()

    def _run_initial_scan(self) -> None:
        # Do not auto-scan an empty path.
        if not self.path_edit.text().strip():
            return

        self._show_busy_dialog("Scanning parent folder...\n\nPlease wait...")

        def _finish() -> None:
            try:
                self._scan_impl()
            except Exception as exc:
                QMessageBox.critical(self, "Scan Failed", str(exc))
            finally:
                self._close_busy_dialog()

        QTimer.singleShot(0, _finish)

    def browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Choose Parent Folder")
        if folder:
            self.path_edit.setText(folder)

    def scan(self) -> None:
        folder = self.path_edit.text().strip()
        if not folder or not Path(folder).exists():
            QMessageBox.warning(self, "Invalid Folder", "Please choose a valid parent folder first.")
            return

        self._show_busy_dialog("Scanning parent folder...\n\nPlease wait...")

        def _finish() -> None:
            try:
                self._scan_impl()
            except Exception as exc:
                QMessageBox.critical(self, "Scan Failed", str(exc))
            finally:
                self._close_busy_dialog()

        QTimer.singleShot(0, _finish)

    def _scan_impl(self) -> None:
        folder = self.path_edit.text().strip()
        if not folder or not Path(folder).exists():
            self.candidates = []
            self.table.setRowCount(0)
            return

        self.candidates = discover_projects(folder, self.depth_spin.value())
        self.table.setRowCount(len(self.candidates))

        for row, candidate in enumerate(self.candidates):
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            check_item.setCheckState(Qt.Checked)
            check_item.setData(Qt.UserRole, candidate.path)
            self.table.setItem(row, 0, check_item)

            self.table.setItem(row, 1, QTableWidgetItem(candidate.name))
            self.table.setItem(row, 2, QTableWidgetItem(candidate.language or "Unknown"))
            self.table.setItem(row, 3, QTableWidgetItem(candidate.framework or ""))
            self.table.setItem(row, 4, QTableWidgetItem("Yes" if candidate.git_enabled else "No"))

            path_item = QTableWidgetItem(candidate.path)
            path_item.setToolTip(candidate.path)
            self.table.setItem(row, 5, path_item)

        self.table.resizeColumnsToContents()

        if not self.candidates:
            QMessageBox.information(self, "Scan Complete", "No likely project folders were found.")

    def _set_all_checks(self, checked: bool) -> None:
        state = Qt.Checked if checked else Qt.Unchecked
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(state)

    def accept_selection(self) -> None:
        selected: list[Project] = []

        for row, candidate in enumerate(self.candidates):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                tags = []
                if candidate.language:
                    tags.append(candidate.language)
                if candidate.framework:
                    tags.append(candidate.framework)

                selected.append(
                    Project(
                        id=None,
                        name=candidate.name,
                        root_path=candidate.path,
                        status="Planning",
                        language=candidate.language,
                        framework=candidate.framework,
                        tags=normalize_tags(", ".join(tags)),
                        git_enabled=candidate.git_enabled,
                        git_branch=candidate.git_branch,
                        remote_url=candidate.remote_url,
                    )
                )

        if not selected:
            QMessageBox.information(self, "Nothing Selected", "Please check at least one project to import.")
            return

        self.projects_to_import = selected
        self.accept()
