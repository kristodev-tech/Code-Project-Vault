from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ActivityPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._all_rows: list[dict] = []

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)

        self.title = QLabel("Recent Activity")
        self.title.setStyleSheet("font-size: 18px; font-weight: bold;")

        self.subtitle = QLabel("Latest activity across all projects")
        self.subtitle.setWordWrap(True)

        # ── Filters ───────────────────────────────────────────────────
        filter_row = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search activity...")
        self.search_edit.textChanged.connect(self.apply_filters)

        self.project_filter = QComboBox()
        self.project_filter.currentIndexChanged.connect(self.apply_filters)

        self.type_filter = QComboBox()
        self.type_filter.currentIndexChanged.connect(self.apply_filters)

        filter_row.addWidget(QLabel("Search:"))
        filter_row.addWidget(self.search_edit, 1)
        filter_row.addWidget(QLabel("Project:"))
        filter_row.addWidget(self.project_filter)
        filter_row.addWidget(QLabel("Type:"))
        filter_row.addWidget(self.type_filter)

        self.activity_list = QListWidget()

        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addLayout(filter_row)
        layout.addWidget(self.activity_list, 1)

        self._reset_filters()

    def _reset_filters(self) -> None:
        self.project_filter.blockSignals(True)
        self.type_filter.blockSignals(True)

        self.project_filter.clear()
        self.project_filter.addItem("All Projects")

        self.type_filter.clear()
        self.type_filter.addItem("All Types")

        self.project_filter.blockSignals(False)
        self.type_filter.blockSignals(False)

    def set_activity(self, rows: list[dict]) -> None:
        self._all_rows = rows or []
        self._populate_filter_values()
        self.apply_filters()

    def _populate_filter_values(self) -> None:
        current_project = self.project_filter.currentText() if self.project_filter.count() else "All Projects"
        current_type = self.type_filter.currentText() if self.type_filter.count() else "All Types"

        project_names = sorted(
            {
                str(row.get("project_name", "Unknown Project")).strip() or "Unknown Project"
                for row in self._all_rows
            },
            key=str.lower,
        )

        activity_types = sorted(
            {
                str(row.get("activity_type", "")).strip()
                for row in self._all_rows
                if str(row.get("activity_type", "")).strip()
            },
            key=str.lower,
        )

        self.project_filter.blockSignals(True)
        self.type_filter.blockSignals(True)

        self.project_filter.clear()
        self.project_filter.addItem("All Projects")
        self.project_filter.addItems(project_names)

        self.type_filter.clear()
        self.type_filter.addItem("All Types")
        self.type_filter.addItems(activity_types)

        project_index = self.project_filter.findText(current_project)
        self.project_filter.setCurrentIndex(project_index if project_index >= 0 else 0)

        type_index = self.type_filter.findText(current_type)
        self.type_filter.setCurrentIndex(type_index if type_index >= 0 else 0)

        self.project_filter.blockSignals(False)
        self.type_filter.blockSignals(False)

    def apply_filters(self) -> None:
        self.activity_list.clear()

        if not self._all_rows:
            self.activity_list.addItem("No activity found.")
            return

        search_text = self.search_edit.text().strip().lower()
        selected_project = self.project_filter.currentText()
        selected_type = self.type_filter.currentText()

        filtered_rows: list[dict] = []

        for row in self._all_rows:
            created_at = str(row.get("created_at", ""))
            project_name = str(row.get("project_name", "Unknown Project")).strip() or "Unknown Project"
            activity_type = str(row.get("activity_type", "")).strip()
            message = str(row.get("message", ""))

            if selected_project != "All Projects" and project_name != selected_project:
                continue

            if selected_type != "All Types" and activity_type != selected_type:
                continue

            haystack = f"{created_at} {project_name} {activity_type} {message}".lower()
            if search_text and search_text not in haystack:
                continue

            filtered_rows.append(row)

        if not filtered_rows:
            self.activity_list.addItem("No matching activity found.")
            return

        for row in filtered_rows:
            created_at = str(row.get("created_at", ""))
            project_name = str(row.get("project_name", "Unknown Project")).strip() or "Unknown Project"
            activity_type = str(row.get("activity_type", "")).strip()
            message = str(row.get("message", ""))

            item = QListWidgetItem(
                f"{created_at} | {project_name} | {activity_type} | {message}"
            )
            item.setToolTip(
                f"Date: {created_at}\n"
                f"Project: {project_name}\n"
                f"Type: {activity_type}\n"
                f"Message: {message}"
            )
            self.activity_list.addItem(item)