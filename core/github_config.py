from __future__ import annotations

import json
from pathlib import Path

from core.settings import APP_DIR


GITHUB_CONFIG_DIR = APP_DIR / "config"
GITHUB_CONFIG_FILE = GITHUB_CONFIG_DIR / "github_app.json"


def _ensure_config_dir() -> None:
    GITHUB_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_github_app_settings() -> dict:
    if not GITHUB_CONFIG_FILE.exists():
        return {}

    try:
        data = json.loads(GITHUB_CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_github_app_settings(client_id: str, slug: str) -> None:
    _ensure_config_dir()
    payload = {
        "client_id": (client_id or "").strip(),
        "slug": (slug or "").strip(),
    }
    GITHUB_CONFIG_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def clear_github_app_settings() -> None:
    if GITHUB_CONFIG_FILE.exists():
        GITHUB_CONFIG_FILE.unlink()


def get_github_client_id() -> str:
    data = load_github_app_settings()
    return str(data.get("client_id", "")).strip()


def get_github_app_slug() -> str:
    data = load_github_app_settings()
    return str(data.get("slug", "")).strip()


def is_github_app_configured() -> bool:
    return bool(get_github_client_id() and get_github_app_slug())