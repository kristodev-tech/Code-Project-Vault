from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.models import ProjectCommand


class CommandDialog(QDialog):
    def __init__(
        self,
        project_path: str,
        parent=None,
        command: ProjectCommand | None = None,
    ):
        super().__init__(parent)

        self.edit_mode = command is not None
        self.original_command = command
        self.command_data: tuple[str, str, str, bool] | None = None

        self.setWindowTitle("Edit Saved Command" if self.edit_mode else "Add Saved Command")
        self.resize(560, 180)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_edit = QLineEdit()
        self.command_edit = QLineEdit()
        self.working_dir_edit = QLineEdit(project_path)
        self.default_check = QCheckBox("Set as default")

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)

        wd_container = QWidget()
        wd_row = QHBoxLayout(wd_container)
        wd_row.setContentsMargins(0, 0, 0, 0)
        wd_row.addWidget(self.working_dir_edit, 1)
        wd_row.addWidget(browse_btn)

        form.addRow("Name:", self.name_edit)
        form.addRow("Command:", self.command_edit)
        form.addRow("Working Dir:", wd_container)
        form.addRow("Options:", self.default_check)
        layout.addLayout(form)

        buttons = QHBoxLayout()
        buttons.addStretch(1)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

        if command is not None:
            self._load_command(command, project_path)

    def _load_command(self, command: ProjectCommand, project_path: str) -> None:
        self.name_edit.setText(command.name or "")
        self.command_edit.setText(command.command or "")
        self.working_dir_edit.setText(command.working_dir or project_path or "")
        self.default_check.setChecked(bool(command.is_default))

    def browse_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Working Folder")
        if folder:
            self.working_dir_edit.setText(folder)

    def save(self) -> None:
        name = self.name_edit.text().strip()
        command = self.command_edit.text().strip()
        working_dir = self.working_dir_edit.text().strip()

        if not name or not command:
            QMessageBox.warning(self, "Missing Information", "Name and command are required.")
            return

        self.command_data = (
            name,
            command,
            working_dir,
            self.default_check.isChecked(),
        )
        self.accept()
