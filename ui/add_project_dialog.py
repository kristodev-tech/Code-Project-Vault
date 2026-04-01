from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QProgressDialog,
    QApplication,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.models import Project
from core.scanner import scan_project_folder
from core.utils import normalize_tags, safe_name_from_path

STATUSES = [
    "Idea", "Planning", "In Progress", "Testing",
    "Beta", "Released", "On Hold", "Archived"
]


class AddProjectDialog(QDialog):
    def __init__(self, parent=None, project: Project | None = None):
        super().__init__(parent)
        self.edit_mode = project is not None
        self.original_project = project
        self.project: Project | None = None
        self._busy_dialog: QProgressDialog | None = None

        self.setWindowTitle("Edit Project" if self.edit_mode else "Add Project")
        self.resize(620, 500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.path_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.notes_edit = QTextEdit()
        self.tags_edit = QLineEdit()
        self.category_edit = QLineEdit()

        self.status_combo = QComboBox()
        self.status_combo.addItems(STATUSES)

        self.favorite_check = QCheckBox("Favorite")
        self.archived_check = QCheckBox("Archived")

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)

        path_container = QWidget()
        path_row = QHBoxLayout(path_container)
        path_row.setContentsMargins(0, 0, 0, 0)
        path_row.addWidget(self.path_edit, 1)
        path_row.addWidget(browse_btn)

        form.addRow("Name:", self.name_edit)
        form.addRow("Folder:", path_container)
        form.addRow("Status:", self.status_combo)
        form.addRow("Category:", self.category_edit)
        form.addRow("Tags:", self.tags_edit)
        form.addRow("Description:", self.description_edit)
        form.addRow("Notes:", self.notes_edit)
        form.addRow("Flags:", self._build_flags_row())

        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        scan_btn = QPushButton("Scan Folder")
        scan_btn.clicked.connect(self.scan_now)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_project)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(scan_btn)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        if project:
            self._load_project(project)

    def _build_flags_row(self) -> QWidget:
        widget = QWidget()
        row = QHBoxLayout(widget)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.favorite_check)
        row.addWidget(self.archived_check)
        row.addStretch(1)
        return widget

    def _show_busy_dialog(self, message: str = "Saving project...\n\nPlease wait...") -> None:
        self._close_busy_dialog()
        self._busy_dialog = QProgressDialog(message, None, 0, 0, self)
        self._busy_dialog.setWindowTitle("Please Wait")
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

    def _load_project(self, project: Project) -> None:
        self.name_edit.setText(project.name)
        self.path_edit.setText(project.root_path)
        self.status_combo.setCurrentText(project.status)
        self.category_edit.setText(project.category)
        self.tags_edit.setText(project.tags)
        self.description_edit.setPlainText(project.description)
        self.notes_edit.setPlainText(project.notes)
        self.favorite_check.setChecked(bool(project.is_favorite))
        self.archived_check.setChecked(bool(project.is_archived))

    def browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Project Folder")
        if not folder:
            return
        self.path_edit.setText(folder)
        if not self.name_edit.text().strip():
            self.name_edit.setText(safe_name_from_path(folder))

    def scan_now(self) -> None:
        folder = self.path_edit.text().strip()
        if not folder or not Path(folder).exists():
            QMessageBox.warning(self, "Invalid Folder", "Please choose a valid project folder first.")
            return

        busy = None
        try:
            busy = QProgressDialog("Scanning folder...\n\nPlease wait...", None, 0, 0, self)
            busy.setWindowTitle("Please Wait")
            busy.setWindowModality(Qt.WindowModal)
            busy.setMinimumDuration(0)
            busy.setAutoClose(False)
            busy.setAutoReset(False)
            busy.setCancelButton(None)
            busy.setValue(0)
            busy.show()
            QApplication.processEvents()

            info = scan_project_folder(folder)
        finally:
            if busy is not None:
                busy.close()
                busy.deleteLater()
                QApplication.processEvents()

        msg = (
            f"Detected language: {info['language'] or 'Unknown'}\n"
            f"Detected framework: {info['framework'] or 'Unknown'}\n"
            f"Git found: {'Yes' if info['git_enabled'] else 'No'}\n"
            f"Git branch: {info['git_branch'] or 'Unknown'}\n"
            f"Remote URL: {info['remote_url'] or 'None'}\n"
            f"Key files: {', '.join(info['key_files']) if info['key_files'] else 'None found'}"
        )
        QMessageBox.information(self, "Scan Result", msg)

    def _build_project(self) -> bool:
        name = self.name_edit.text().strip()
        root_path = self.path_edit.text().strip()

        if not name or not root_path:
            self._close_busy_dialog()
            QMessageBox.warning(self, "Missing Information", "Name and folder path are required.")
            return False

        if not Path(root_path).exists():
            self._close_busy_dialog()
            QMessageBox.warning(self, "Invalid Folder", "Selected folder does not exist.")
            return False

        scan = scan_project_folder(root_path)

        self.project = Project(
            id=self.original_project.id if self.original_project else None,
            name=name,
            root_path=root_path,
            description=self.description_edit.toPlainText().strip(),
            notes=self.notes_edit.toPlainText().strip(),
            status=self.status_combo.currentText(),
            language=scan["language"],
            framework=scan["framework"],
            category=self.category_edit.text().strip(),
            tags=normalize_tags(self.tags_edit.text()),
            is_favorite=1 if self.favorite_check.isChecked() else 0,
            is_archived=1 if self.archived_check.isChecked() else 0,
            git_enabled=scan["git_enabled"],
            git_branch=scan["git_branch"],
            remote_url=scan["remote_url"],
            last_scanned_at="",
        )
        return True

    def save_project(self) -> None:
        self._show_busy_dialog("Saving project...\n\nPlease wait...")

        def _finish_save() -> None:
            try:
                ok = self._build_project()
                if not ok:
                    return

                self._close_busy_dialog()
                self.accept()
            except Exception as exc:
                self._close_busy_dialog()
                QMessageBox.critical(self, "Save Failed", str(exc))

        QTimer.singleShot(0, _finish_save)
