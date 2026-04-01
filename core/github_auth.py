from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.github_config import (
    get_github_app_slug,
    get_github_client_id,
    is_github_app_configured,
)
from core.settings import APP_DIR


DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
API_BASE = "https://api.github.com"
APP_USER_AGENT = "Project Vault"

# NOTE:
# Starter implementation stores session locally.
# Later, this should move to Windows Credential Manager for production.
AUTH_DIR = APP_DIR / "auth"
AUTH_FILE = AUTH_DIR / "github_session.json"


@dataclass
class GitHubSession:
    access_token: str
    refresh_token: str
    expires_at: str
    refresh_token_expires_at: str
    token_type: str = "bearer"

    def expires_soon(self, within_minutes: int = 10) -> bool:
        try:
            expires_dt = datetime.fromisoformat(self.expires_at)
        except Exception:
            return True
        return datetime.now(timezone.utc) + timedelta(minutes=within_minutes) >= expires_dt


class GitHubAuthError(RuntimeError):
    pass


def _ensure_auth_dir() -> None:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)


def _url_quote(value: str) -> str:
    from urllib.parse import quote_plus
    return quote_plus(value)


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    payload = "&".join(f"{k}={_url_quote(v)}" for k, v in data.items()).encode("utf-8")
    req = Request(
        url,
        data=payload,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": APP_USER_AGENT,
        },
        method="POST",
    )
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise GitHubAuthError(f"GitHub auth request failed: {exc.code} {body}") from exc


def _api_request(
    method: str,
    path: str,
    token: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any]:
    url = path if path.startswith("http") else f"{API_BASE}{path}"
    body = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": APP_USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = Request(url, data=body, headers=headers, method=method.upper())
    try:
        with urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        raise GitHubAuthError(f"GitHub API request failed: {exc.code} {body_text}") from exc


def is_configured() -> bool:
    return is_github_app_configured()


def start_device_flow() -> dict[str, Any]:
    client_id = get_github_client_id()
    slug = get_github_app_slug()

    if not client_id or not slug:
        raise GitHubAuthError(
            "GitHub App is not configured yet. Open GitHub Settings and enter your Client ID and App Slug first."
        )

    return _post_form(
        DEVICE_CODE_URL,
        {
            "client_id": client_id,
        },
    )


def poll_for_user_token(
    device_code: str,
    interval_seconds: int,
    timeout_seconds: int = 900,
) -> GitHubSession:
    client_id = get_github_client_id()
    slug = get_github_app_slug()

    if not client_id or not slug:
        raise GitHubAuthError("GitHub App is not configured.")

    deadline = time.time() + timeout_seconds
    poll_interval = max(1, interval_seconds)

    while time.time() < deadline:
        data = _post_form(
            ACCESS_TOKEN_URL,
            {
                "client_id": client_id,
                "device_code": device_code,
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            },
        )

        if "access_token" in data:
            session = GitHubSession(
                access_token=data["access_token"],
                refresh_token=data.get("refresh_token", ""),
                expires_at=_expires_to_iso(data.get("expires_in", 0)),
                refresh_token_expires_at=_expires_to_iso(data.get("refresh_token_expires_in", 0)),
                token_type=data.get("token_type", "bearer"),
            )
            save_session(session)
            return session

        error = data.get("error", "")
        if error == "authorization_pending":
            time.sleep(poll_interval)
            continue
        if error == "slow_down":
            poll_interval += 5
            time.sleep(poll_interval)
            continue
        if error in {"expired_token", "access_denied", "unsupported_grant_type", "incorrect_device_code"}:
            raise GitHubAuthError(f"GitHub device flow failed: {error}")

        time.sleep(poll_interval)

    raise GitHubAuthError("Timed out waiting for GitHub authorization.")


def refresh_user_token(session: GitHubSession) -> GitHubSession:
    client_id = get_github_client_id()
    if not session.refresh_token:
        raise GitHubAuthError("No refresh token is available.")
    if not client_id:
        raise GitHubAuthError("GitHub App client ID is not configured.")

    data = _post_form(
        ACCESS_TOKEN_URL,
        {
            "client_id": client_id,
            "grant_type": "refresh_token",
            "refresh_token": session.refresh_token,
        },
    )

    if "access_token" not in data:
        raise GitHubAuthError("Failed to refresh GitHub user token.")

    new_session = GitHubSession(
        access_token=data["access_token"],
        refresh_token=data.get("refresh_token", session.refresh_token),
        expires_at=_expires_to_iso(data.get("expires_in", 0)),
        refresh_token_expires_at=_expires_to_iso(data.get("refresh_token_expires_in", 0)),
        token_type=data.get("token_type", "bearer"),
    )
    save_session(new_session)
    return new_session


def _expires_to_iso(seconds: int) -> str:
    dt = datetime.now(timezone.utc) + timedelta(seconds=int(seconds or 0))
    return dt.isoformat()


def save_session(session: GitHubSession) -> None:
    _ensure_auth_dir()
    AUTH_FILE.write_text(
        json.dumps(
            {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expires_at": session.expires_at,
                "refresh_token_expires_at": session.refresh_token_expires_at,
                "token_type": session.token_type,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def load_session() -> GitHubSession | None:
    if not AUTH_FILE.exists():
        return None

    try:
        data = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
        return GitHubSession(
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            expires_at=data.get("expires_at", ""),
            refresh_token_expires_at=data.get("refresh_token_expires_at", ""),
            token_type=data.get("token_type", "bearer"),
        )
    except Exception:
        return None


def clear_session() -> None:
    if AUTH_FILE.exists():
        AUTH_FILE.unlink()


def get_valid_access_token() -> str:
    session = load_session()
    if not session:
        raise GitHubAuthError("No GitHub session found. Connect GitHub first.")

    if session.expires_soon():
        session = refresh_user_token(session)

    return session.access_token


def get_authenticated_user() -> dict[str, Any]:
    token = get_valid_access_token()
    data = _api_request("GET", "/user", token)
    return data if isinstance(data, dict) else {}


def list_user_installations() -> list[dict[str, Any]]:
    token = get_valid_access_token()
    data = _api_request("GET", "/user/installations", token)
    if isinstance(data, dict):
        return list(data.get("installations", []))
    return []


def get_install_url_for_user() -> str:
    slug = get_github_app_slug()
    if not slug:
        return ""
    return f"https://github.com/apps/{slug}/installations/new"


def open_in_browser(url: str) -> None:
    if not url:
        return
    try:
        import webbrowser
        webbrowser.open(url)
    except Exception:
        subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)