from __future__ import annotations

import re

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QTextEdit,
    QVBoxLayout,
)

from core.github_auth import GitHubAuthError, get_authenticated_user, is_configured, list_user_installations
from core.github_publish import (
    GitHubPublishError,
    get_current_branch,
    is_git_repo,
    publish_project,
)
from core.models import Project


def _safe_repo_name(value: str) -> str:
    value = value.strip().replace(" ", "-")
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "new-repository"


class GitHubPublishDialog(QDialog):
    def __init__(self, project: Project, parent=None):
        super().__init__(parent)

        self.project = project
        self.connected_login = ""
        self.installations: list[dict] = []

        self.setWindowTitle("Publish to GitHub")
        self.resize(760, 620)

        layout = QVBoxLayout(self)

        title = QLabel("Publish to GitHub")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)

        form = QFormLayout()

        self.owner_type_combo = QComboBox()
        self.owner_type_combo.addItem("My GitHub Account", "user")
        self.owner_type_combo.addItem("Organization", "org")
        self.owner_type_combo.currentIndexChanged.connect(self._update_owner_mode)

        self.owner_name_edit = QLineEdit()
        self.owner_name_edit.setPlaceholderText("Organization name")

        self.repo_name_edit = QLineEdit(_safe_repo_name(project.name or ""))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(90)
        self.description_edit.setPlainText(project.description or "")

        self.visibility_combo = QComboBox()
        self.visibility_combo.addItem("Private", True)
        self.visibility_combo.addItem("Public", False)

        self.init_git_check = QCheckBox("Initialize Git if this project is not already a Git repository")
        self.init_git_check.setChecked(True)

        self.commit_message_edit = QLineEdit("Initial commit")

        form.addRow("Owner:", self.owner_type_combo)
        form.addRow("Organization:", self.owner_name_edit)
        form.addRow("Repository Name:", self.repo_name_edit)
        form.addRow("Description:", self.description_edit)
        form.addRow("Visibility:", self.visibility_combo)
        form.addRow("Git Setup:", self.init_git_check)
        form.addRow("Initial Commit Message:", self.commit_message_edit)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(True)

        button_row = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh GitHub Info")
        self.refresh_btn.clicked.connect(self.refresh_github_info)

        self.publish_btn = QPushButton("Publish")
        self.publish_btn.clicked.connect(self.publish_now)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)

        button_row.addWidget(self.refresh_btn)
        button_row.addStretch(1)
        button_row.addWidget(self.publish_btn)
        button_row.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(self.summary_label)
        layout.addLayout(form)
        layout.addWidget(self.info_browser, 1)
        layout.addLayout(button_row)

        self._update_owner_mode()
        self.refresh_github_info()

    def _update_owner_mode(self) -> None:
        owner_type = self.owner_type_combo.currentData()
        self.owner_name_edit.setEnabled(owner_type == "org")
        if owner_type != "org":
            self.owner_name_edit.clear()

    def refresh_github_info(self) -> None:
        if not is_configured():
            self.summary_label.setText("GitHub App settings are not configured yet.")
            self.info_browser.setHtml(
                "<h3>GitHub Not Configured</h3>"
                "<p>Open <b>GitHub Settings</b> in Project Vault and enter your GitHub App Client ID and Slug first.</p>"
            )
            return

        try:
            user = get_authenticated_user()
            self.connected_login = str(user.get("login", "")).strip()
            self.installations = list_user_installations()

            git_enabled = is_git_repo(self.project.root_path)
            branch = get_current_branch(self.project.root_path) if git_enabled else "(not initialized)"

            self.summary_label.setText(
                f"Project: {self.project.name}\n"
                f"Folder: {self.project.root_path}\n"
                f"Git Enabled: {'Yes' if git_enabled else 'No'}\n"
                f"Current Branch: {branch}\n"
                f"Connected GitHub User: {self.connected_login or 'Unknown'}"
            )

            installs_html = "<ul>"
            if self.installations:
                for item in self.installations:
                    account = item.get("account", {}) or {}
                    login = str(account.get("login", "")).strip() or "Unknown"
                    installs_html += f"<li>{login}</li>"
                installs_html += "</ul>"
            else:
                installs_html = (
                    "<p><b>No GitHub App installations were found.</b><br>"
                    "You must install the configured GitHub App into your account or organization before publishing.</p>"
                )

            self.info_browser.setHtml(
                f"""
                <h3>GitHub Publish Readiness</h3>
                <p><b>Connected account:</b> {self.connected_login or 'Unknown'}</p>
                <p><b>Detected app installations:</b></p>
                {installs_html}
                <p><b>Publish behavior:</b></p>
                <ul>
                  <li>If Git is not initialized and the checkbox is enabled, Project Vault will initialize Git first.</li>
                  <li>If no commit exists yet, Project Vault will create the first commit using the message you provide.</li>
                  <li>Project Vault will create the repository on GitHub, add/update <b>origin</b>, and push the current branch.</li>
                </ul>
                """
            )

        except Exception as exc:
            self.summary_label.setText("GitHub connection is required before publishing.")
            self.info_browser.setHtml(
                "<h3>Not Ready</h3>"
                f"<p>{str(exc)}</p>"
                "<p>Configure GitHub Settings and connect GitHub first.</p>"
            )

    def publish_now(self) -> None:
        if not is_configured():
            QMessageBox.warning(
                self,
                "GitHub Not Configured",
                "Open GitHub Settings and enter your GitHub App Client ID and Slug first."
            )
            return

        repo_name = _safe_repo_name(self.repo_name_edit.text())
        description = self.description_edit.toPlainText().strip()
        private = bool(self.visibility_combo.currentData())
        owner_type = str(self.owner_type_combo.currentData() or "user")
        owner_name = self.owner_name_edit.text().strip()
        init_git_if_needed = self.init_git_check.isChecked()
        commit_message = self.commit_message_edit.text().strip() or "Initial commit"

        if not repo_name:
            QMessageBox.warning(self, "Missing Repository Name", "Enter a repository name.")
            return

        if owner_type == "org" and not owner_name:
            QMessageBox.warning(self, "Missing Organization", "Enter an organization name.")
            return

        try:
            result = publish_project(
                project_path=self.project.root_path,
                repo_name=repo_name,
                owner_type=owner_type,
                owner_name=owner_name,
                description=description,
                private=private,
                commit_message=commit_message,
                init_git_if_needed=init_git_if_needed,
            )

            repo_url = result.get("repo_url", "")
            branch = result.get("branch", "")

            QMessageBox.information(
                self,
                "Publish Complete",
                f"Repository published successfully.\n\n"
                f"Repository: {repo_url}\n"
                f"Branch: {branch}"
            )
            self.accept()

        except (GitHubPublishError, GitHubAuthError) as exc:
            QMessageBox.critical(self, "Publish Failed", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Publish Failed", str(exc))