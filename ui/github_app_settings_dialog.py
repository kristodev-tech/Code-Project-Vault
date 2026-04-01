from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from core.github_auth import clear_session
from core.github_config import (
    clear_github_app_settings,
    get_github_app_slug,
    get_github_client_id,
    is_github_app_configured,
    save_github_app_settings,
)


class GitHubAppSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("GitHub Settings")
        self.resize(720, 500)

        layout = QVBoxLayout(self)

        title = QLabel("GitHub Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        form = QFormLayout()

        self.client_id_edit = QLineEdit()
        self.slug_edit = QLineEdit()

        form.addRow("GitHub App Client ID:", self.client_id_edit)
        form.addRow("GitHub App Slug:", self.slug_edit)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(True)

        button_row = QHBoxLayout()

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_settings)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_settings)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_row.addWidget(self.save_btn)
        button_row.addWidget(self.clear_btn)
        button_row.addStretch(1)
        button_row.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addLayout(form)
        layout.addWidget(self.info_browser, 1)
        layout.addLayout(button_row)

        self.refresh_ui()

    def refresh_ui(self) -> None:
        self.client_id_edit.setText(get_github_client_id())
        self.slug_edit.setText(get_github_app_slug())

        configured = is_github_app_configured()
        self.status_label.setText(
            "GitHub is configured for this PC." if configured
            else "GitHub is not configured yet on this PC."
        )

        self.info_browser.setHtml(
            """
            <h3>How to use this</h3>
            <p>Enter the values from your GitHub App registration:</p>
            <ul>
              <li><b>Client ID</b> from the GitHub App settings page</li>
              <li><b>Slug</b> from the GitHub App URL or settings page</li>
            </ul>
            <p>These settings are saved locally on this computer for the current user.</p>
            <p>Examples:</p>
            <ul>
              <li>Client ID: <code>Iv23abc123Example</code></li>
              <li>Slug: <code>project-vault-desktop</code></li>
            </ul>
            <p>If you clear these settings, the saved GitHub login session will also be removed.</p>
            """
        )

    def save_settings(self) -> None:
        client_id = self.client_id_edit.text().strip()
        slug = self.slug_edit.text().strip()

        if not client_id or not slug:
            QMessageBox.warning(
                self,
                "Missing Information",
                "Both GitHub App Client ID and GitHub App Slug are required."
            )
            return

        save_github_app_settings(client_id, slug)
        clear_session()
        self.refresh_ui()

        QMessageBox.information(
            self,
            "GitHub Settings Saved",
            "GitHub settings were saved locally.\n\n"
            "If you were previously connected, sign in again so the new settings take effect."
        )

    def clear_settings(self) -> None:
        answer = QMessageBox.question(
            self,
            "Clear GitHub Settings",
            "Clear the saved GitHub App settings and remove the saved GitHub login session?"
        )
        if answer != QMessageBox.Yes:
            return

        clear_github_app_settings()
        clear_session()
        self.refresh_ui()

        QMessageBox.information(
            self,
            "GitHub Settings Cleared",
            "Saved GitHub App settings and session were removed."
        )