from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from core.github_auth import (
    GitHubAuthError,
    clear_session,
    get_authenticated_user,
    get_install_url_for_user,
    is_configured,
    list_user_installations,
    load_session,
    open_in_browser,
    poll_for_user_token,
    start_device_flow,
)


class GitHubConnectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Connect GitHub")
        self.resize(720, 520)

        self.device_code = ""
        self.poll_interval = 5
        self.verification_uri = ""
        self.user_code = ""

        layout = QVBoxLayout(self)

        title = QLabel("Connect GitHub")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.info_browser = QTextBrowser()
        self.info_browser.setOpenExternalLinks(True)

        button_row_1 = QHBoxLayout()
        self.start_btn = QPushButton("Start Sign-In")
        self.start_btn.clicked.connect(self.start_sign_in)

        self.open_browser_btn = QPushButton("Open GitHub Device Page")
        self.open_browser_btn.clicked.connect(self.open_device_page)
        self.open_browser_btn.setEnabled(False)

        self.finish_btn = QPushButton("Finish Sign-In")
        self.finish_btn.clicked.connect(self.finish_sign_in)
        self.finish_btn.setEnabled(False)

        button_row_1.addWidget(self.start_btn)
        button_row_1.addWidget(self.open_browser_btn)
        button_row_1.addWidget(self.finish_btn)
        button_row_1.addStretch(1)

        button_row_2 = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh Account Info")
        self.refresh_btn.clicked.connect(self.refresh_account_info)

        self.install_btn = QPushButton("Install GitHub App")
        self.install_btn.clicked.connect(self.open_install_page)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_github)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_row_2.addWidget(self.refresh_btn)
        button_row_2.addWidget(self.install_btn)
        button_row_2.addWidget(self.disconnect_btn)
        button_row_2.addStretch(1)
        button_row_2.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(self.status_label)
        layout.addWidget(self.info_browser, 1)
        layout.addLayout(button_row_1)
        layout.addLayout(button_row_2)

        self.refresh_account_info()

    def _set_info_html(self, html: str) -> None:
        self.info_browser.setHtml(html)

    def start_sign_in(self) -> None:
        if not is_configured():
            QMessageBox.warning(
                self,
                "GitHub Not Configured",
                "GitHub App settings are not configured yet.\n\n"
                "Open GitHub Settings and enter your Client ID and App Slug first."
            )
            return

        try:
            data = start_device_flow()
            self.device_code = str(data.get("device_code", "")).strip()
            self.user_code = str(data.get("user_code", "")).strip()
            self.verification_uri = str(
                data.get("verification_uri") or data.get("verification_uri_complete") or ""
            ).strip()
            self.poll_interval = int(data.get("interval", 5) or 5)

            if not self.device_code or not self.user_code or not self.verification_uri:
                raise GitHubAuthError("GitHub device flow did not return the required fields.")

            self.open_browser_btn.setEnabled(True)
            self.finish_btn.setEnabled(True)

            self.status_label.setText(
                "Step 1: Open the GitHub device page.\n"
                "Step 2: Enter the code shown below.\n"
                "Step 3: Approve access.\n"
                "Step 4: Return here and click 'Finish Sign-In'."
            )

            self._set_info_html(
                f"""
                <h3>Device Sign-In</h3>
                <p><b>Verification URL:</b><br>{self.verification_uri}</p>
                <p><b>User Code:</b><br><span style="font-size:20px; font-weight:bold;">{self.user_code}</span></p>
                <p>Use <b>Open GitHub Device Page</b> to continue in your browser.</p>
                """
            )

            open_in_browser(self.verification_uri)

        except Exception as exc:
            QMessageBox.critical(self, "GitHub Sign-In Failed", str(exc))

    def open_device_page(self) -> None:
        if self.verification_uri:
            open_in_browser(self.verification_uri)

    def finish_sign_in(self) -> None:
        if not self.device_code:
            QMessageBox.information(self, "No Sign-In Started", "Start GitHub sign-in first.")
            return

        try:
            self.status_label.setText("Waiting for GitHub authorization to complete...")
            session = poll_for_user_token(
                device_code=self.device_code,
                interval_seconds=self.poll_interval,
                timeout_seconds=180,
            )
            _ = session
            self.device_code = ""
            self.user_code = ""
            self.verification_uri = ""
            self.open_browser_btn.setEnabled(False)
            self.finish_btn.setEnabled(False)

            self.refresh_account_info()
            QMessageBox.information(self, "GitHub Connected", "GitHub sign-in completed successfully.")

        except Exception as exc:
            QMessageBox.critical(self, "GitHub Sign-In Failed", str(exc))
            self.refresh_account_info()

    def refresh_account_info(self) -> None:
        session = load_session()
        if not is_configured():
            self.status_label.setText("GitHub App settings are not configured yet.")
            self._set_info_html(
                "<h3>GitHub Not Configured</h3>"
                "<p>Open <b>GitHub Settings</b> in Project Vault and enter your GitHub App Client ID and Slug first.</p>"
            )
            return

        if not session:
            self.status_label.setText("GitHub is not connected.")
            install_url = get_install_url_for_user()
            install_html = f'<p><a href="{install_url}">Install the GitHub App</a></p>' if install_url else ""
            self._set_info_html(
                "<h3>Not Connected</h3>"
                "<p>Use <b>Start Sign-In</b> to connect your GitHub account.</p>"
                + install_html
            )
            return

        try:
            user = get_authenticated_user()
            login = str(user.get("login", "")).strip() or "Unknown"
            name = str(user.get("name", "")).strip()
            html_url = str(user.get("html_url", "")).strip()

            installs = list_user_installations()
            install_count = len(installs)

            self.status_label.setText(f"Connected to GitHub as {login}")

            installs_html = ""
            if installs:
                installs_html += "<h4>Accessible Installations</h4><ul>"
                for item in installs:
                    account = item.get("account", {}) or {}
                    account_login = str(account.get("login", "")).strip() or "Unknown"
                    installs_html += f"<li>{account_login}</li>"
                installs_html += "</ul>"
            else:
                installs_html = (
                    "<p><b>No GitHub App installations were found yet.</b><br>"
                    "Install the configured GitHub App into your account or organization before publishing.</p>"
                )

            profile_html = f'<p><b>Profile:</b> <a href="{html_url}">{html_url}</a></p>' if html_url else ""

            self._set_info_html(
                f"""
                <h3>Connected</h3>
                <p><b>Login:</b> {login}</p>
                <p><b>Name:</b> {name or 'Not set'}</p>
                <p><b>Installations found:</b> {install_count}</p>
                {profile_html}
                {installs_html}
                """
            )

        except Exception as exc:
            self.status_label.setText("GitHub session exists, but account info could not be loaded.")
            self._set_info_html(
                "<h3>Connection Problem</h3>"
                f"<p>{str(exc)}</p>"
                "<p>You can try <b>Refresh Account Info</b> or sign in again.</p>"
            )

    def open_install_page(self) -> None:
        url = get_install_url_for_user()
        if not url:
            QMessageBox.information(
                self,
                "GitHub Not Configured",
                "GitHub App settings are not configured yet."
            )
            return
        open_in_browser(url)

    def disconnect_github(self) -> None:
        answer = QMessageBox.question(
            self,
            "Disconnect GitHub",
            "Remove the saved GitHub session from this PC?"
        )
        if answer != QMessageBox.Yes:
            return

        clear_session()
        self.device_code = ""
        self.user_code = ""
        self.verification_uri = ""
        self.open_browser_btn.setEnabled(False)
        self.finish_btn.setEnabled(False)
        self.refresh_account_info()