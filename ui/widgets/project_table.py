from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableWidget, QTableWidgetItem

from core.models import Project
from core.project_types import get_project_type_badge


class ProjectTable(QTableWidget):
    project_selected = Signal(int)
    project_context_menu_requested = Signal(int, QPoint)
    project_activated = Signal(int)

    def __init__(self, parent=None):
        super().__init__(0, 8, parent)

        self.setHorizontalHeaderLabels([
            "Type",
            "★",
            "Name",
            "Status",
            "Language",
            "Framework",
            "Tags",
            "Path",
        ])

        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(False)

        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.Interactive)
        header.setSectionResizeMode(7, QHeaderView.Stretch)

        self.setColumnWidth(0, 130)
        self.setColumnWidth(6, 160)

        # ── Enable click-to-sort on headers ──────────────────────────
        self.setSortingEnabled(True)
        header.setSortIndicatorShown(True)

        # ── Enable right-click context menu on rows ──────────────────
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_context_menu_requested)

    def set_projects(self, projects: list[Project]) -> None:
        current_id = self.current_project_id()

        sorting_enabled = self.isSortingEnabled()
        self.setSortingEnabled(False)

        self.clearContents()
        self.setRowCount(len(projects))

        selected_row = 0

        for row, project in enumerate(projects):
            values = [
                get_project_type_badge(project),
                "★" if project.is_favorite else "",
                project.name or "",
                project.status or "",
                project.language or "",
                project.framework or "",
                project.tags or "",
                project.root_path or "",
            ]

            for col, value in enumerate(values):
                item = QTableWidgetItem(value)

                if col == 1:
                    item.setTextAlignment(Qt.AlignCenter)

                if col in (6, 7):
                    item.setToolTip(value)

                if col == 0:
                    item.setToolTip(value)

                item.setData(Qt.UserRole, project.id)
                self.setItem(row, col, item)

            if current_id is not None and project.id == current_id:
                selected_row = row

        self.resizeRowsToContents()

        if self.rowCount():
            self.selectRow(selected_row)

        self.setSortingEnabled(sorting_enabled)

    def current_project_id(self) -> int | None:
        items = self.selectedItems()
        if not items:
            return None
        project_id = items[0].data(Qt.UserRole)
        return int(project_id) if project_id is not None else None

    def _on_selection_changed(self) -> None:
        project_id = self.current_project_id()
        if project_id is not None:
            self.project_selected.emit(project_id)

    def _on_item_double_clicked(self, item) -> None:
        if item is None:
            return

        project_id = item.data(Qt.UserRole)
        if project_id is not None:
            self.project_activated.emit(int(project_id))

    def _on_context_menu_requested(self, pos: QPoint) -> None:
        item = self.itemAt(pos)
        if item is None:
            return

        row = item.row()
        self.selectRow(row)

        row_item = self.item(row, 0)
        if row_item is None:
            return

        project_id = row_item.data(Qt.UserRole)
        if project_id is None:
            return

        global_pos = self.viewport().mapToGlobal(pos)
        self.project_context_menu_requested.emit(int(project_id), global_pos)
