from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QGuiApplication, QCursor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from core.launcher import open_folder, open_in_vscode, open_terminal, open_powershell
from core.models import Project
from core.project_service import (
    ProjectService,
    add_project,
    add_project_command,
    dashboard_stats,
    delete_project,
    delete_project_command,
    export_backup_json,
    get_project,
    get_project_command,
    import_backup_json,
    import_projects,
    list_all_activity,
    list_categories,
    list_project_commands,
    list_projects,
    list_statuses,
    list_tags,
    rescan_project,
    run_saved_command,
    set_archived,
    toggle_favorite,
    update_last_opened,
    update_project,
    update_project_command,
)
from ui.activity_panel import ActivityPanel
from ui.add_project_dialog import AddProjectDialog
from ui.command_dialog import CommandDialog
from ui.github_app_settings_dialog import GitHubAppSettingsDialog
from ui.github_connect_dialog import GitHubConnectDialog
from ui.github_publish_dialog import GitHubPublishDialog
from ui.help_dialog import HelpDialog
from ui.import_projects_dialog import ImportProjectsDialog
from ui.project_detail_panel import ProjectDetailPanel
from ui.widgets.project_table import ProjectTable


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        icon_path = Path(__file__).resolve().parents[1] / "assets" / "icons" / "project_vault_icon_128.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setWindowTitle("Code Project Vault")

        self.current_project: Project | None = None
        self.current_view = "projects"
        self.service = ProjectService()
        self._startup_geometry_applied = False

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        # ── Row 1: title + filters ────────────────────────────────────────────
        title = QLabel("Project Vault")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search projects...")
        self.search_edit.textChanged.connect(self.refresh_projects)

        self.tag_filter = QComboBox()
        self.tag_filter.setMinimumWidth(130)
        self.tag_filter.currentIndexChanged.connect(self.refresh_projects)

        self.status_filter = QComboBox()
        self.status_filter.setMinimumWidth(120)
        self.status_filter.currentIndexChanged.connect(self.refresh_projects)

        self.favorites_only = QCheckBox("Favorites Only")
        self.favorites_only.stateChanged.connect(self.refresh_projects)

        self.show_archived = QCheckBox("Show Archived")
        self.show_archived.stateChanged.connect(self.refresh_projects)

        filter_row = QHBoxLayout()
        filter_row.addWidget(title)
        filter_row.addSpacing(12)
        filter_row.addWidget(QLabel("Search:"))
        filter_row.addWidget(self.search_edit, 1)
        filter_row.addWidget(QLabel("Tag:"))
        filter_row.addWidget(self.tag_filter, 0)
        filter_row.addWidget(QLabel("Status:"))
        filter_row.addWidget(self.status_filter, 0)
        filter_row.addWidget(self.favorites_only)
        filter_row.addWidget(self.show_archived)
        root.addLayout(filter_row)

        # ── Row 2: project actions ────────────────────────────────────────────
        self.add_btn = QPushButton("Add Project")
        self.add_btn.clicked.connect(self.add_project_dialog)

        self.scan_btn = QPushButton("Scan Parent Folder")
        self.scan_btn.clicked.connect(self.scan_parent_folder)

        self.github_settings_btn = QPushButton("GitHub Settings")
        self.github_settings_btn.clicked.connect(self.open_github_settings_dialog)

        self.github_connect_btn = QPushButton("Connect GitHub")
        self.github_connect_btn.clicked.connect(self.open_github_connect_dialog)

        self.github_publish_btn = QPushButton("Publish to GitHub")
        self.github_publish_btn.clicked.connect(self.open_github_publish_dialog)

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_project_dialog)

        self.favorite_btn = QPushButton("Favorite")
        self.favorite_btn.clicked.connect(self.toggle_favorite_selected)

        self.archive_btn = QPushButton("Archive / Restore")
        self.archive_btn.clicked.connect(self.toggle_archive_selected)

        self.delete_btn = QPushButton("Delete")
        self.delete_btn.clicked.connect(self.delete_selected)

        project_actions_row = QHBoxLayout()
        project_actions_row.addWidget(self.add_btn)
        project_actions_row.addWidget(self.scan_btn)
        project_actions_row.addWidget(self.github_settings_btn)
        project_actions_row.addWidget(self.github_connect_btn)
        project_actions_row.addWidget(self.github_publish_btn)
        project_actions_row.addWidget(self.edit_btn)
        project_actions_row.addWidget(self.favorite_btn)
        project_actions_row.addWidget(self.archive_btn)
        project_actions_row.addWidget(self.delete_btn)
        project_actions_row.addStretch(1)
        root.addLayout(project_actions_row)

        # ── Stats row ──────────────────────────────────────────────────────────
        stats_row = QHBoxLayout()

        self.stats_total = QLabel()
        self.stats_active = QLabel()
        self.stats_archived = QLabel()
        self.stats_favorites = QLabel()
        self.stats_git = QLabel()

        for widget in [
            self.stats_total,
            self.stats_active,
            self.stats_archived,
            self.stats_favorites,
            self.stats_git,
        ]:
            widget.setStyleSheet("padding: 6px 10px; border: 1px solid #777; border-radius: 6px;")
            widget.setMinimumHeight(34)
            widget.setMaximumHeight(34)
            widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
            stats_row.addWidget(widget, 0, Qt.AlignTop)

        stats_row.addStretch(1)
        root.addLayout(stats_row)

        # ── Row 3: launch tools ───────────────────────────────────────────────
        self.open_folder_btn = QPushButton("Open Folder")
        self.open_folder_btn.clicked.connect(self.do_open_folder)

        self.open_code_btn = QPushButton("Open VS Code")
        self.open_code_btn.clicked.connect(self.do_open_code)

        self.open_terminal_btn = QPushButton("Open CMD")
        self.open_terminal_btn.clicked.connect(self.do_open_terminal)

        self.open_powershell_btn = QPushButton("Open PowerShell")
        self.open_powershell_btn.clicked.connect(self.do_open_powershell)

        self.rescan_btn = QPushButton("Re-Scan Project")
        self.rescan_btn.clicked.connect(self.rescan_selected_project)

        launch_row = QHBoxLayout()
        launch_row.addWidget(self.open_folder_btn)
        launch_row.addWidget(self.open_code_btn)
        launch_row.addWidget(self.open_terminal_btn)
        launch_row.addWidget(self.open_powershell_btn)
        launch_row.addWidget(self.rescan_btn)
        launch_row.addStretch(1)
        root.addLayout(launch_row)

        # ── Row 4: command + backup actions ───────────────────────────────────
        self.add_command_btn = QPushButton("Add Command")
        self.add_command_btn.clicked.connect(self.add_command)

        self.edit_command_btn = QPushButton("Edit Selected Command")
        self.edit_command_btn.clicked.connect(self.edit_selected_command)

        self.command_select = QComboBox()
        self.command_select.setMinimumWidth(200)
        self.command_select.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.run_selected_command_btn = QPushButton("Run Selected Command")
        self.run_selected_command_btn.clicked.connect(self.run_selected_command)

        self.run_command_btn = QPushButton("Run Default Command")
        self.run_command_btn.clicked.connect(self.run_default_command)

        self.delete_command_btn = QPushButton("Delete Selected Command")
        self.delete_command_btn.clicked.connect(self.delete_selected_command)

        self.export_btn = QPushButton("Export Backup")
        self.export_btn.clicked.connect(self.export_backup)

        self.import_btn = QPushButton("Import Backup")
        self.import_btn.clicked.connect(self.import_backup)

        command_row = QHBoxLayout()
        command_row.addWidget(self.add_command_btn)
        command_row.addWidget(QLabel("Saved Command:"))
        command_row.addWidget(self.command_select, 1)
        command_row.addWidget(self.edit_command_btn)
        command_row.addWidget(self.run_selected_command_btn)
        command_row.addWidget(self.run_command_btn)
        command_row.addWidget(self.delete_command_btn)
        command_row.addWidget(self.export_btn)
        command_row.addWidget(self.import_btn)
        root.addLayout(command_row)

        # ── Main splitter ──────────────────────────────────────────────────────
        main_splitter = QSplitter(Qt.Horizontal)

        sidebar_widget = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_widget)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)

        nav_title = QLabel("Views")
        nav_title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.nav_list = QListWidget()
        self.nav_list.addItem("Projects")
        self.nav_list.addItem("Activity")
        self.nav_list.currentTextChanged.connect(self.on_nav_changed)
        self.nav_list.setMaximumWidth(260)

        sidebar_title = QLabel("Categories")
        sidebar_title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.category_list = QListWidget()
        self.category_list.currentTextChanged.connect(self.refresh_projects)
        self.category_list.setMinimumWidth(180)
        self.category_list.setMaximumWidth(260)

        sidebar_layout.addWidget(nav_title)
        sidebar_layout.addWidget(self.nav_list)
        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(self.category_list)

        self.project_splitter = QSplitter(Qt.Horizontal)

        self.table = ProjectTable()
        self.details = ProjectDetailPanel()
        self.table.project_selected.connect(self.load_project_details)
        self.table.project_context_menu_requested.connect(self.show_project_context_menu)
        self.table.project_activated.connect(self.open_project_from_table)

        self.project_splitter.addWidget(self.table)
        self.project_splitter.addWidget(self.details)
        self.project_splitter.setStretchFactor(0, 4)
        self.project_splitter.setStretchFactor(1, 1)
        self.project_splitter.setSizes([820, 340])

        self.activity_panel = ActivityPanel()

        self.content_host = QWidget()
        self.content_host.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        content_layout = QVBoxLayout(self.content_host)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self.project_splitter, 1)
        content_layout.addWidget(self.activity_panel, 1)

        self.activity_panel.hide()

        main_splitter.addWidget(sidebar_widget)
        main_splitter.addWidget(self.content_host)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        root.addWidget(main_splitter, 1)

        self._build_menus()
        self._build_status_bar()

    def _build_menus(self) -> None:
        menubar = self.menuBar()

        help_menu = menubar.addMenu("Help")

        help_action = QAction("View Help", self)
        help_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(help_action)

        about_action = QAction("About Project Vault", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _build_status_bar(self) -> None:
        status = QStatusBar(self)
        self.setStatusBar(status)

        self.status_project_label = QLabel("No project selected")
        self.statusBar().addPermanentWidget(self.status_project_label)

        self.show_status_message("Ready")

    def _target_screen_geometry(self):
        screen = self.windowHandle().screen() if self.windowHandle() else None
        if screen is None:
            screen = QGuiApplication.screenAt(QCursor.pos())
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        if screen is None:
            return None
        return screen.availableGeometry()

    def _size_and_center_window(self) -> None:
        available = self._target_screen_geometry()
        if available is None:
            self.resize(1570, 820)
            return

        screen_width = available.width()
        screen_height = available.height()

        target_width = int(screen_width * 0.86)
        target_height = int(screen_height * 0.84)

        target_width = max(1100, min(target_width, 1570))
        target_height = max(720, min(target_height, screen_height - 80))

        x = available.x() + (available.width() - target_width) // 2
        y = available.y() + (available.height() - target_height) // 2

        self.setGeometry(x, y, target_width, target_height)

    def _apply_startup_geometry_once(self) -> None:
        if self._startup_geometry_applied:
            return

        self._startup_geometry_applied = True
        self.setWindowState(self.windowState() & ~Qt.WindowMaximized)
        self.showNormal()
        self._size_and_center_window()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._apply_startup_geometry_once)

    def show_status_message(self, message: str, timeout_ms: int = 4000) -> None:
        self.statusBar().showMessage(message, timeout_ms)

    def _update_status_project_label(self) -> None:
        if self.current_project:
            self.status_project_label.setText(f"Selected: {self.current_project.name}")
        else:
            self.status_project_label.setText("No project selected")

    def show_help_dialog(self) -> None:
        dlg = HelpDialog(self)
        dlg.exec()

    def show_about_dialog(self) -> None:
        QMessageBox.information(
            self,
            "About Project Vault",
            "Project Vault\n\n"
            "A desktop application for organizing, launching, inspecting, tracking, and publishing code projects from one place.\n\n"
            "Current features include:\n"
            "- project organization and filtering\n"
            "- category, tag, and status views\n"
            "- sortable project table\n"
            "- right-click project actions\n"
            "- double-click to open project folder\n"
            "- launch tools for Folder, VS Code, CMD, and PowerShell\n"
            "- README preview with Markdown rendering\n"
            "- local Git status and commit details\n"
            "- saved commands with add, edit, run, and delete support\n"
            "- recent activity tracking\n"
            "- backup export/import\n"
            "- status bar feedback\n"
            "- GitHub settings, connection, and publish workflow\n\n"
            "GitHub publishing is user-configured.\n"
            "Each user must create or use their own GitHub App, then enter their own GitHub App Client ID and App Slug in GitHub Settings."
        )

    def _finish_startup(self, loading_dialog=None) -> None:
        if loading_dialog is not None:
            loading_dialog.setLabelText("Loading categories...")
            QApplication.processEvents()

        self.refresh_category_list()

        if loading_dialog is not None:
            loading_dialog.setLabelText("Preparing views...")
            QApplication.processEvents()

        self.nav_list.setCurrentRow(0)

        if loading_dialog is not None:
            loading_dialog.setLabelText("Loading tags and statuses...")
            QApplication.processEvents()

        self.refresh_tag_filter()
        self.refresh_status_filter()

        if loading_dialog is not None:
            loading_dialog.setLabelText("Loading projects...")
            QApplication.processEvents()

        self.refresh_projects()
        self.refresh_dashboard()
        self.table.viewport().update()
        self.show_status_message("Project Vault loaded")

        if loading_dialog is not None:
            loading_dialog.setLabelText("Finalizing startup...")
            QApplication.processEvents()

    def refresh_filters_and_projects(self) -> None:
        self.refresh_category_list()
        self.refresh_tag_filter()
        self.refresh_status_filter()
        self.refresh_projects()

    def refresh_after_project_change(
        self,
        project_id: int | None = None,
        clear_all_cache: bool = False,
        invalidate_details_cache: bool = False,
        warm_cache: bool = False,
        refresh_activity: bool = False,
    ) -> None:
        if clear_all_cache:
            self.details.clear_all_cache()

        if invalidate_details_cache and project_id is not None:
            self.details.invalidate_project_cache(project_id)

        self.refresh_filters_and_projects()

        if warm_cache and project_id is not None:
            self.details.warm_project_cache(project_id)

        if project_id is not None:
            self.load_project_details(project_id)

        if refresh_activity and self.current_view == "activity":
            self.refresh_activity_view()

    def refresh_after_command_change(
        self,
        project_id: int,
        refresh_activity: bool = True,
        restore_command_id: int | None = None,
    ) -> None:
        self.details.invalidate_project_cache(project_id)
        self.load_project_details(project_id)
        self.refresh_command_selector(project_id)

        if restore_command_id is not None:
            for idx in range(self.command_select.count()):
                if self.command_select.itemData(idx) == restore_command_id:
                    self.command_select.setCurrentIndex(idx)
                    break

        if refresh_activity and self.current_view == "activity":
            self.refresh_activity_view()

    def refresh_command_selector(self, project_id: int | None = None) -> None:
        self.command_select.blockSignals(True)
        self.command_select.clear()

        if project_id is None:
            self.command_select.addItem("No commands saved", None)
            self.command_select.blockSignals(False)
            return

        commands = list_project_commands(project_id)
        if not commands:
            self.command_select.addItem("No commands saved", None)
            self.command_select.blockSignals(False)
            return

        for cmd in commands:
            label = cmd.name
            if cmd.is_default:
                label += " [default]"
            self.command_select.addItem(label, cmd.id)

        self.command_select.blockSignals(False)

    def refresh_current_view(self) -> None:
        if self.current_view == "activity":
            self.refresh_activity_view()
        else:
            self.refresh_projects()

    def refresh_dashboard(self) -> None:
        stats = dashboard_stats()
        self.stats_total.setText(f"Total: {stats['total']}")
        self.stats_active.setText(f"Active: {stats['active']}")
        self.stats_archived.setText(f"Archived: {stats['archived']}")
        self.stats_favorites.setText(f"Favorites: {stats['favorites']}")
        self.stats_git.setText(f"Git Projects: {stats['git_enabled']}")

    def refresh_tag_filter(self) -> None:
        current = self.tag_filter.currentText()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("All Tags")
        self.tag_filter.addItems(list_tags())
        index = self.tag_filter.findText(current)
        self.tag_filter.setCurrentIndex(index if index >= 0 else 0)
        self.tag_filter.blockSignals(False)

    def refresh_category_list(self) -> None:
        current = self.category_list.currentItem().text() if self.category_list.currentItem() else "All Categories"

        self.category_list.blockSignals(True)
        self.category_list.clear()
        self.category_list.addItem("All Categories")
        self.category_list.addItems(list_categories())

        matches = self.category_list.findItems(current, Qt.MatchExactly)
        if matches:
            self.category_list.setCurrentItem(matches[0])
        else:
            self.category_list.setCurrentRow(0)

        self.category_list.blockSignals(False)

    def refresh_status_filter(self) -> None:
        current = self.status_filter.currentText()
        self.status_filter.blockSignals(True)
        self.status_filter.clear()
        self.status_filter.addItem("All Statuses")
        self.status_filter.addItems(list_statuses())
        index = self.status_filter.findText(current)
        self.status_filter.setCurrentIndex(index if index >= 0 else 0)
        self.status_filter.blockSignals(False)

    def on_nav_changed(self, text: str) -> None:
        if text == "Activity":
            self.show_activity_view()
        else:
            self.show_projects_view()

    def show_projects_view(self) -> None:
        self.current_view = "projects"

        self.activity_panel.hide()
        self.project_splitter.show()

        def _restore_layout():
            self.project_splitter.setSizes([780, 360])
            self.content_host.updateGeometry()
            self.project_splitter.updateGeometry()
            self.table.updateGeometry()
            self.details.updateGeometry()
            self.refresh_projects()

        QTimer.singleShot(0, _restore_layout)
        self.show_status_message("Projects view")

    def show_activity_view(self) -> None:
        self.current_view = "activity"

        self.project_splitter.hide()
        self.activity_panel.show()

        def _refresh_layout():
            self.content_host.updateGeometry()
            self.activity_panel.updateGeometry()
            self.refresh_activity_view()

        QTimer.singleShot(0, _refresh_layout)
        self.show_status_message("Activity view")

    def refresh_activity_view(self) -> None:
        rows = list_all_activity(limit=250)
        self.activity_panel.set_activity(rows)

    def refresh_projects(self) -> None:
        selected_id = self.table.current_project_id()
        current_id = self.current_project.id if self.current_project else None
        preferred_id = selected_id if selected_id is not None else current_id

        current_category = self.category_list.currentItem().text() if self.category_list.currentItem() else "All Categories"

        projects = list_projects(
            search_text=self.search_edit.text(),
            tag_filter=self.tag_filter.currentText() or "All Tags",
            status_filter=self.status_filter.currentText() or "All Statuses",
            category_filter=current_category,
            show_archived=self.show_archived.isChecked(),
            favorites_only=self.favorites_only.isChecked(),
        )

        self.table.set_projects(projects)
        self.refresh_dashboard()

        if not projects:
            self.current_project = None
            self.details.set_project(None)
            self.refresh_command_selector(None)
            self._update_status_project_label()
            return

        chosen_id = None
        if preferred_id is not None:
            for project in projects:
                if project.id == preferred_id:
                    chosen_id = project.id
                    break

        if chosen_id is None:
            chosen_id = projects[0].id

        self.load_project_details(chosen_id)

    def add_project_dialog(self) -> None:
        dlg = AddProjectDialog(self)
        if dlg.exec() and dlg.project:
            try:
                new_project_id = add_project(dlg.project)

                self.refresh_after_project_change(
                    project_id=new_project_id,
                    clear_all_cache=True,
                    warm_cache=True,
                )
                self.show_status_message(f"Project added: {dlg.project.name}")

            except Exception as exc:
                QMessageBox.critical(self, "Save Failed", str(exc))
                self.show_status_message("Add project failed")

    def edit_project_dialog(self) -> None:
        project = self._require_project()
        if not project:
            return

        dlg = AddProjectDialog(self, project=project)
        if dlg.exec() and dlg.project:
            try:
                update_project(dlg.project)

                self.refresh_after_project_change(
                    project_id=dlg.project.id,
                    invalidate_details_cache=True,
                    warm_cache=True,
                )
                self.show_status_message(f"Project updated: {dlg.project.name}")

            except Exception as exc:
                QMessageBox.critical(self, "Update Failed", str(exc))
                self.show_status_message("Project update failed")

    def scan_parent_folder(self) -> None:
        dlg = ImportProjectsDialog(self)
        if dlg.exec() and dlg.projects_to_import:
            busy = None
            try:
                busy = QProgressDialog(
                    "Importing detected projects...\n\nPlease wait...",
                    None,
                    0,
                    0,
                    self,
                )
                busy.setWindowTitle("Importing Projects")
                busy.setWindowModality(Qt.WindowModal)
                busy.setMinimumDuration(0)
                busy.setAutoClose(False)
                busy.setAutoReset(False)
                busy.setCancelButton(None)
                busy.setValue(0)
                busy.show()
                QApplication.processEvents()

                added, skipped = import_projects(dlg.projects_to_import)

                self.refresh_after_project_change(clear_all_cache=True)

                QMessageBox.information(
                    self,
                    "Import Complete",
                    f"Added: {added}\nSkipped (already existed): {skipped}"
                )
                self.show_status_message(f"Import complete: {added} added, {skipped} skipped")

            except Exception as exc:
                QMessageBox.critical(self, "Import Failed", str(exc))
                self.show_status_message("Project import failed")
            finally:
                if busy is not None:
                    busy.close()
                    busy.deleteLater()
                    QApplication.processEvents()

    def rescan_selected_project(self) -> None:
        project = self._require_project()
        if not project:
            return

        busy = None
        try:
            busy = QProgressDialog(
                f"Re-scanning '{project.name}'...\n\nPlease wait...",
                None,
                0,
                0,
                self,
            )
            busy.setWindowTitle("Re-Scanning Project")
            busy.setWindowModality(Qt.WindowModal)
            busy.setMinimumDuration(0)
            busy.setAutoClose(False)
            busy.setAutoReset(False)
            busy.setCancelButton(None)
            busy.setValue(0)
            busy.show()
            QApplication.processEvents()

            rescan_project(project.id)

            self.refresh_after_project_change(
                project_id=project.id,
                invalidate_details_cache=True,
                warm_cache=True,
                refresh_activity=True,
            )

            QMessageBox.information(
                self,
                "Re-Scan Complete",
                f"Project '{project.name}' was re-scanned."
            )
            self.show_status_message(f"Project re-scanned: {project.name}")

        except Exception as exc:
            QMessageBox.warning(self, "Re-Scan Failed", str(exc))
            self.show_status_message("Project re-scan failed")
        finally:
            if busy is not None:
                busy.close()
                busy.deleteLater()
                QApplication.processEvents()

    def load_project_details(self, project_id: int | None) -> None:
        if project_id is None:
            self.current_project = None
            self.details.set_project(None)
            self.refresh_command_selector(None)
            self._update_status_project_label()
            return

        project = get_project(project_id)
        if not project:
            self.current_project = None
            self.details.set_project(None)
            self.refresh_command_selector(None)
            self._update_status_project_label()
            return

        self.current_project = project
        self.details.set_project(project)
        self.refresh_command_selector(project.id)
        self._update_status_project_label()

    def open_project_from_table(self, project_id: int) -> None:
        self.load_project_details(project_id)
        self.do_open_folder()

    def _require_project(self) -> Project | None:
        project_id = self.table.current_project_id()
        if project_id is not None:
            self.current_project = get_project(project_id)

        if not self.current_project:
            QMessageBox.information(self, "No Project Selected", "Please select a project first.")
            return None

        return self.current_project

    def open_github_settings_dialog(self) -> None:
        dlg = GitHubAppSettingsDialog(self)
        dlg.exec()
        self.show_status_message("GitHub settings dialog closed")

    def open_github_connect_dialog(self) -> None:
        dlg = GitHubConnectDialog(self)
        dlg.exec()
        self.show_status_message("GitHub connection dialog closed")

    def open_github_publish_dialog(self) -> None:
        project = self._require_project()
        if not project:
            return

        dlg = GitHubPublishDialog(project, self)
        if dlg.exec():
            self.show_status_message(f"Published to GitHub: {project.name}")
            try:
                self.rescan_selected_project()
            except Exception:
                pass

    def show_project_context_menu(self, project_id: int, global_pos) -> None:
        project = get_project(project_id)
        if not project:
            return

        self.current_project = project
        self.load_project_details(project_id)

        menu = QMenu(self)

        open_folder_action = menu.addAction("Open Folder")
        open_code_action = menu.addAction("Open VS Code")
        open_cmd_action = menu.addAction("Open CMD")
        open_powershell_action = menu.addAction("Open PowerShell")

        menu.addSeparator()

        favorite_text = "Remove Favorite" if project.is_favorite else "Mark Favorite"
        archive_text = "Restore Project" if project.is_archived else "Archive Project"

        favorite_action = menu.addAction(favorite_text)
        archive_action = menu.addAction(archive_text)

        menu.addSeparator()

        edit_action = menu.addAction("Edit Project")
        rescan_action = menu.addAction("Re-Scan Project")

        menu.addSeparator()

        delete_action = menu.addAction("Delete Project")

        chosen = menu.exec(global_pos)
        if chosen is None:
            return

        if chosen == open_folder_action:
            self.do_open_folder()
        elif chosen == open_code_action:
            self.do_open_code()
        elif chosen == open_cmd_action:
            self.do_open_terminal()
        elif chosen == open_powershell_action:
            self.do_open_powershell()
        elif chosen == favorite_action:
            self.toggle_favorite_selected()
        elif chosen == archive_action:
            self.toggle_archive_selected()
        elif chosen == edit_action:
            self.edit_project_dialog()
        elif chosen == rescan_action:
            self.rescan_selected_project()
        elif chosen == delete_action:
            self.delete_selected()

    def toggle_favorite_selected(self) -> None:
        project = self._require_project()
        if not project:
            return

        toggle_favorite(project.id)
        self.refresh_projects()

        project_name = project.name
        updated = get_project(project.id)
        if updated and updated.is_favorite:
            self.show_status_message(f"Marked favorite: {project_name}")
        else:
            self.show_status_message(f"Removed favorite: {project_name}")

    def toggle_archive_selected(self) -> None:
        project = self._require_project()
        if not project:
            return

        archived = not bool(project.is_archived)
        set_archived(project.id, archived)
        self.refresh_filters_and_projects()

        if archived:
            self.show_status_message(f"Archived: {project.name}")
        else:
            self.show_status_message(f"Restored: {project.name}")

    def delete_selected(self) -> None:
        project = self._require_project()
        if not project:
            return

        project_name = project.name

        answer = QMessageBox.question(
            self,
            "Delete Project",
            f"Delete '{project_name}' from Project Vault?\n\nThis removes it from the app database only.",
        )
        if answer != QMessageBox.Yes:
            return

        delete_project(project.id)
        self.current_project = None
        self.refresh_filters_and_projects()
        self.show_status_message(f"Deleted project: {project_name}")

    def do_open_folder(self) -> None:
        project = self._require_project()
        if not project:
            return

        try:
            open_folder(project.root_path)
            update_last_opened(project.id)
            self.refresh_current_view()
            self.show_status_message(f"Opened folder: {project.name}")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Open Folder Failed",
                f"Could not open this project folder.\n\n{exc}"
            )
            self.show_status_message("Open folder failed")

    def do_open_code(self) -> None:
        project = self._require_project()
        if not project:
            return

        try:
            open_in_vscode(project.root_path)
            update_last_opened(project.id)
            self.service.record_activity(project.id, "open_vscode", "Opened in VS Code")
            self.refresh_current_view()
            self.show_status_message(f"Opened in VS Code: {project.name}")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "VS Code Launch Failed",
                f"Could not open this project in VS Code.\n\n{exc}"
            )
            self.show_status_message("VS Code launch failed")

    def do_open_terminal(self) -> None:
        project = self._require_project()
        if not project:
            return

        try:
            open_terminal(project.root_path)
            update_last_opened(project.id)
            self.refresh_current_view()
            self.show_status_message(f"Opened CMD: {project.name}")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Terminal Launch Failed",
                f"Could not open CMD for this project.\n\n{exc}"
            )
            self.show_status_message("CMD launch failed")

    def do_open_powershell(self) -> None:
        project = self._require_project()
        if not project:
            return

        try:
            open_powershell(project.root_path)
            update_last_opened(project.id)
            self.refresh_current_view()
            self.show_status_message(f"Opened PowerShell: {project.name}")
        except Exception as exc:
            QMessageBox.warning(
                self,
                "PowerShell Launch Failed",
                f"Could not open PowerShell for this project.\n\n{exc}"
            )
            self.show_status_message("PowerShell launch failed")

    def add_command(self) -> None:
        project = self._require_project()
        if not project:
            return

        dlg = CommandDialog(project.root_path, self)
        if dlg.exec() and dlg.command_data:
            name, command, working_dir, is_default = dlg.command_data
            add_project_command(project.id, name, command, working_dir, is_default)

            self.refresh_after_command_change(project.id)
            self.show_status_message(f"Command added: {name}")

    def edit_selected_command(self) -> None:
        project = self._require_project()
        if not project:
            return

        command_id = self.command_select.currentData()
        if command_id is None:
            QMessageBox.information(self, "No Command Selected", "Please select a saved command first.")
            return

        command = get_project_command(command_id)
        if not command:
            QMessageBox.information(self, "Command Not Found", "The selected command could not be found.")
            return

        dlg = CommandDialog(project.root_path, self, command=command)
        if dlg.exec() and dlg.command_data:
            name, command_text, working_dir, is_default = dlg.command_data
            update_project_command(command.id, name, command_text, working_dir, is_default)

            self.refresh_after_command_change(
                project.id,
                restore_command_id=command.id,
            )
            self.show_status_message(f"Command updated: {name}")

    def run_selected_command(self) -> None:
        project = self._require_project()
        if not project:
            return

        command_id = self.command_select.currentData()
        if command_id is None:
            QMessageBox.information(self, "No Command Selected", "Please select a saved command first.")
            return

        ok, message = run_saved_command(command_id)
        if ok:
            QMessageBox.information(self, "Command Started", message)
            self.refresh_after_command_change(project.id)
            self.show_status_message(message)
        else:
            QMessageBox.warning(self, "Command Failed", message)
            self.show_status_message("Command failed")

    def run_default_command(self) -> None:
        project = self._require_project()
        if not project:
            return

        commands = list_project_commands(project.id)
        if not commands:
            QMessageBox.information(self, "No Commands", "This project has no saved commands yet.")
            return

        command = next((c for c in commands if c.is_default), commands[0])
        ok, message = run_saved_command(command.id)

        if ok:
            QMessageBox.information(self, "Command Started", message)
            self.refresh_after_command_change(project.id)
            self.show_status_message(message)
        else:
            QMessageBox.warning(self, "Command Failed", message)
            self.show_status_message("Command failed")

    def delete_selected_command(self) -> None:
        project = self._require_project()
        if not project:
            return

        command_id = self.command_select.currentData()
        if command_id is None:
            QMessageBox.information(self, "No Command Selected", "Please select a saved command to delete.")
            return

        commands = list_project_commands(project.id)
        command = next((c for c in commands if c.id == command_id), None)
        if not command:
            QMessageBox.information(self, "Command Not Found", "The selected command could not be found.")
            return

        answer = QMessageBox.question(
            self,
            "Delete Command",
            f"Delete command '{command.name}'?"
        )
        if answer != QMessageBox.Yes:
            return

        delete_project_command(command.id)
        self.refresh_after_command_change(project.id)
        self.show_status_message(f"Command deleted: {command.name}")

    def export_backup(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Backup",
            "project_vault_backup.json",
            "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            p, c, a = export_backup_json(file_path)
            QMessageBox.information(self, "Backup Exported", f"Projects: {p}\nCommands: {c}\nActivity rows: {a}")
            self.show_status_message(f"Backup exported: {Path(file_path).name}")
        except Exception as exc:
            QMessageBox.warning(self, "Export Failed", str(exc))
            self.show_status_message("Backup export failed")

    def import_backup(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Backup",
            "",
            "JSON Files (*.json)"
        )
        if not file_path:
            return

        try:
            p, c, a = import_backup_json(file_path)
            self.refresh_filters_and_projects()
            if self.current_view == "activity":
                self.refresh_activity_view()
            QMessageBox.information(self, "Backup Imported", f"Projects added: {p}\nCommands added: {c}\nActivity rows added: {a}")
            self.show_status_message(f"Backup imported: {Path(file_path).name}")
        except Exception as exc:
            QMessageBox.warning(self, "Import Failed", str(exc))
            self.show_status_message("Backup import failed")