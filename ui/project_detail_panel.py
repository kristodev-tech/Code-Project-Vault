from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices

from core.models import Project
from core.project_types import get_project_type_badge
from core.project_service import (
    get_project_git_snapshot,
    get_project_key_files,
    get_project_readme_path,
    get_project_readme_text,
    get_project_recent_files,
    list_project_activity,
    list_project_commands,
)


class ProjectDetailPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setMinimumWidth(360)
        self.setMaximumWidth(480)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        self.current_readme_path = ""
        self._git_cache: dict[int, dict] = {}
        self._readme_cache: dict[int, tuple[str, str]] = {}
        self._key_files_cache: dict[int, list[tuple[str, str]]] = {}
        self._recent_files_cache: dict[int, list[tuple[str, str]]] = {}

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        container = QWidget()
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout = QVBoxLayout(container)

        # ── Title row ────────────────────────────────────────────────
        title_row = QHBoxLayout()

        self.type_badge = QLabel("📦 App")
        self.type_badge.setStyleSheet(
            "font-size: 13px; font-weight: bold; "
            "padding: 4px 8px; border: 1px solid #777; border-radius: 8px;"
        )
        self.type_badge.setAlignment(Qt.AlignCenter)
        self.type_badge.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)

        self.title = QLabel("Select a project")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.title.setWordWrap(True)
        self.title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        title_row.addWidget(self.type_badge, 0, Qt.AlignLeft)
        title_row.addWidget(self.title, 1, Qt.AlignLeft)

        self.meta = QLabel("")
        self.meta.setWordWrap(True)
        self.meta.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.meta.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.description = QTextEdit()
        self.description.setReadOnly(True)
        self.description.setMinimumHeight(90)
        self.description.setMaximumHeight(140)
        self.description.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.notes = QTextEdit()
        self.notes.setReadOnly(True)
        self.notes.setMinimumHeight(90)
        self.notes.setMaximumHeight(140)
        self.notes.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.commands_list = QListWidget()
        self.commands_list.setMinimumHeight(90)
        self.commands_list.setMaximumHeight(140)
        self.commands_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.key_files_list = QListWidget()
        self.key_files_list.setMinimumHeight(110)
        self.key_files_list.setMaximumHeight(170)
        self.key_files_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.key_files_list.itemDoubleClicked.connect(self.open_key_file)

        self.recent_files_list = QListWidget()
        self.recent_files_list.setMinimumHeight(90)
        self.recent_files_list.setMaximumHeight(140)
        self.recent_files_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.activity_list = QListWidget()
        self.activity_list.setMinimumHeight(110)
        self.activity_list.setMaximumHeight(170)
        self.activity_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ── Git Section ───────────────────────────────────────────────
        self.git_group = QGroupBox("Git")
        self.git_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        git_layout = QVBoxLayout(self.git_group)

        self.git_enabled_label = QLabel("Git Enabled: No")
        self.git_branch_label = QLabel("Branch: Unknown")
        self.git_remote_label = QLabel("Remote: None")
        self.git_status_label = QLabel("Status: Unknown")
        self.git_modified_label = QLabel("Modified Files: 0")
        self.git_untracked_label = QLabel("Untracked Files: 0")
        self.git_ahead_behind_label = QLabel("Ahead/Behind: Unknown")
        self.git_commit_hash_label = QLabel("Last Commit: None")
        self.git_commit_message_label = QLabel("Commit Message: None")
        self.git_commit_author_label = QLabel("Commit Author: None")
        self.git_commit_date_label = QLabel("Commit Date: None")

        for lbl in [
            self.git_enabled_label,
            self.git_branch_label,
            self.git_remote_label,
            self.git_status_label,
            self.git_modified_label,
            self.git_untracked_label,
            self.git_ahead_behind_label,
            self.git_commit_hash_label,
            self.git_commit_message_label,
            self.git_commit_author_label,
            self.git_commit_date_label,
        ]:
            lbl.setWordWrap(True)
            lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            git_layout.addWidget(lbl)

        # ── README Preview ────────────────────────────────────────────
        self.readme_group = QGroupBox("README Preview")
        self.readme_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        readme_layout = QVBoxLayout(self.readme_group)

        self.readme_path_label = QLabel("README: None")
        self.readme_path_label.setWordWrap(True)
        self.readme_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.readme_path_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        readme_button_row = QHBoxLayout()
        self.open_readme_btn = QPushButton("Open README")
        self.copy_readme_path_btn = QPushButton("Copy README Path")

        self.open_readme_btn.clicked.connect(self.open_readme_file)
        self.copy_readme_path_btn.clicked.connect(self.copy_readme_path)

        readme_button_row.addWidget(self.open_readme_btn)
        readme_button_row.addWidget(self.copy_readme_path_btn)
        readme_button_row.addStretch(1)

        self.readme_preview = QTextBrowser()
        self.readme_preview.setOpenExternalLinks(True)
        self.readme_preview.setOpenLinks(True)
        self.readme_preview.setMinimumHeight(160)
        self.readme_preview.setMaximumHeight(260)
        self.readme_preview.setPlaceholderText("No README found for this project.")
        self.readme_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.readme_preview.setStyleSheet("""
            QTextBrowser {
                padding: 8px;
            }
        """)

        readme_layout.addWidget(self.readme_path_label)
        readme_layout.addLayout(readme_button_row)
        readme_layout.addWidget(self.readme_preview)

        layout.addLayout(title_row)
        layout.addWidget(self.meta)

        layout.addWidget(self.git_group)

        layout.addWidget(QLabel("Description"))
        layout.addWidget(self.description)

        layout.addWidget(QLabel("Notes"))
        layout.addWidget(self.notes)

        layout.addWidget(self.readme_group)

        layout.addWidget(QLabel("Key Files"))
        layout.addWidget(self.key_files_list)

        layout.addWidget(QLabel("Saved Commands"))
        layout.addWidget(self.commands_list)

        layout.addWidget(QLabel("Recent Modified Files"))
        layout.addWidget(self.recent_files_list)

        layout.addWidget(QLabel("Recent Activity"))
        layout.addWidget(self.activity_list)

        layout.addStretch(1)

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        self._update_readme_buttons()

    def warm_project_cache(self, project_id: int) -> None:
        self._get_cached_git_snapshot(project_id)
        self._get_cached_readme(project_id)
        self._get_cached_key_files(project_id)
        self._get_cached_recent_files(project_id, limit=12)

    def _get_cached_git_snapshot(self, project_id: int) -> dict:
        cached = self._git_cache.get(project_id)
        if cached is not None:
            return cached

        data = get_project_git_snapshot(project_id)
        self._git_cache[project_id] = data
        return data

    def _get_cached_readme(self, project_id: int) -> tuple[str, str]:
        cached = self._readme_cache.get(project_id)
        if cached is not None:
            return cached

        readme_path = get_project_readme_path(project_id)
        readme_text = get_project_readme_text(project_id)
        data = (readme_path, readme_text)

        self._readme_cache[project_id] = data
        return data

    def _get_cached_key_files(self, project_id: int) -> list[tuple[str, str]]:
        cached = self._key_files_cache.get(project_id)
        if cached is not None:
            return cached

        data = get_project_key_files(project_id)
        self._key_files_cache[project_id] = data
        return data

    def _get_cached_recent_files(self, project_id: int, limit: int = 12) -> list[tuple[str, str]]:
        cached = self._recent_files_cache.get(project_id)
        if cached is not None:
            return cached

        data = get_project_recent_files(project_id, limit=limit)
        self._recent_files_cache[project_id] = data
        return data

    def invalidate_project_cache(self, project_id: int) -> None:
        self._git_cache.pop(project_id, None)
        self._readme_cache.pop(project_id, None)
        self._key_files_cache.pop(project_id, None)
        self._recent_files_cache.pop(project_id, None)

    def clear_all_cache(self) -> None:
        self._git_cache.clear()
        self._readme_cache.clear()
        self._key_files_cache.clear()
        self._recent_files_cache.clear()

    def _update_readme_buttons(self) -> None:
        has_readme = bool(self.current_readme_path)
        self.open_readme_btn.setEnabled(has_readme)
        self.copy_readme_path_btn.setEnabled(has_readme)

    def _reset_copy_readme_button(self) -> None:
        self.copy_readme_path_btn.setText("Copy README Path")
        self._update_readme_buttons()

    def _set_readme_preview(self, readme_path: str, readme_text: str) -> None:
        if not readme_text:
            self.readme_preview.clear()
            self.readme_preview.setPlaceholderText("No README found for this project.")
            return

        lower_path = (readme_path or "").lower()

        if lower_path.endswith(".md"):
            self.readme_preview.setMarkdown(readme_text)
        else:
            self.readme_preview.setPlainText(readme_text)

    def set_project(self, project: Project | None) -> None:
        if not project:
            self.type_badge.setText("📦 App")
            self.title.setText("Select a project")
            self.meta.setText("")
            self.description.setPlainText("")
            self.notes.setPlainText("")
            self.readme_path_label.setText("README: None")
            self.readme_preview.clear()
            self.readme_preview.setPlaceholderText("No project selected.")
            self.key_files_list.clear()
            self.commands_list.clear()
            self.recent_files_list.clear()
            self.activity_list.clear()

            self.current_readme_path = ""
            self._update_readme_buttons()

            self.git_enabled_label.setText("Git Enabled: No")
            self.git_branch_label.setText("Branch: Unknown")
            self.git_remote_label.setText("Remote: None")
            self.git_status_label.setText("Status: Unknown")
            self.git_modified_label.setText("Modified Files: 0")
            self.git_untracked_label.setText("Untracked Files: 0")
            self.git_ahead_behind_label.setText("Ahead/Behind: Unknown")
            self.git_commit_hash_label.setText("Last Commit: None")
            self.git_commit_message_label.setText("Commit Message: None")
            self.git_commit_author_label.setText("Commit Author: None")
            self.git_commit_date_label.setText("Commit Date: None")
            return

        tag_text = project.tags or "None"
        git = self._get_cached_git_snapshot(project.id)
        readme_path, readme_text = self._get_cached_readme(project.id)
        key_files = self._get_cached_key_files(project.id)
        recent_files = self._get_cached_recent_files(project.id, limit=12)

        self.type_badge.setText(get_project_type_badge(project))
        self.title.setText(project.name)
        self.meta.setText(
            f"Status: {project.status}\n"
            f"Language: {project.language or 'Unknown'}\n"
            f"Framework: {project.framework or 'Unknown'}\n"
            f"Category: {project.category or 'None'}\n"
            f"Tags: {tag_text}\n"
            f"Path: {project.root_path}\n"
            f"Favorite: {'Yes' if project.is_favorite else 'No'}\n"
            f"Archived: {'Yes' if project.is_archived else 'No'}\n"
            f"Last opened: {project.last_opened_at or 'Never'}\n"
            f"Last scanned: {project.last_scanned_at or 'Never'}"
        )

        self.git_enabled_label.setText(f"Git Enabled: {'Yes' if git.get('git_enabled') else 'No'}")
        self.git_branch_label.setText(f"Branch: {git.get('branch') or 'Unknown'}")
        self.git_remote_label.setText(f"Remote: {git.get('remote') or 'None'}")
        self.git_status_label.setText(f"Status: {git.get('status_summary') or 'Unknown'}")
        self.git_modified_label.setText(f"Modified Files: {git.get('modified_count', 0)}")
        self.git_untracked_label.setText(f"Untracked Files: {git.get('untracked_count', 0)}")
        self.git_ahead_behind_label.setText(f"Ahead/Behind: {git.get('ahead_behind') or 'Unknown'}")
        self.git_commit_hash_label.setText(
            f"Last Commit: {git.get('last_commit_short_hash') or git.get('last_commit_hash') or 'None'}"
        )
        self.git_commit_message_label.setText(
            f"Commit Message: {git.get('last_commit_message') or 'None'}"
        )
        self.git_commit_author_label.setText(
            f"Commit Author: {git.get('last_commit_author') or 'None'}"
        )
        self.git_commit_date_label.setText(
            f"Commit Date: {git.get('last_commit_date') or 'None'}"
        )

        self.description.setPlainText(project.description or "")
        self.notes.setPlainText(project.notes or "")

        self.current_readme_path = readme_path or ""
        self._update_readme_buttons()

        if readme_path:
            self.readme_path_label.setText(f"README: {readme_path}")
        else:
            self.readme_path_label.setText("README: None found")

        self._set_readme_preview(readme_path, readme_text)

        self.key_files_list.clear()
        for rel_path, full_path in key_files:
            self.key_files_list.addItem(rel_path)
            self.key_files_list.item(self.key_files_list.count() - 1).setData(Qt.UserRole, full_path)

        self.commands_list.clear()
        for cmd in list_project_commands(project.id):
            default = " [default]" if cmd.is_default else ""
            wd = f" | {cmd.working_dir}" if cmd.working_dir else ""
            self.commands_list.addItem(f"{cmd.name}{default}: {cmd.command}{wd}")

        self.recent_files_list.clear()
        for rel_path, modified_at in recent_files:
            self.recent_files_list.addItem(f"{modified_at} | {rel_path}")

        self.activity_list.clear()
        for act in list_project_activity(project.id, limit=20):
            self.activity_list.addItem(f"{act.created_at} | {act.activity_type} | {act.message}")

    def open_key_file(self, item) -> None:
        full_path = item.data(Qt.UserRole)
        if full_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(full_path))

    def open_readme_file(self) -> None:
        if self.current_readme_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_readme_path))

    def copy_readme_path(self) -> None:
        if not self.current_readme_path:
            return

        QApplication.clipboard().setText(self.current_readme_path)

        self.copy_readme_path_btn.setText("Copied!")
        self.copy_readme_path_btn.setEnabled(False)

        QTimer.singleShot(1200, self._reset_copy_readme_button)