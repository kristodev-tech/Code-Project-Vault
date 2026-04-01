from pathlib import Path
import os

APP_NAME = "Project Vault"

LOCAL_APPDATA = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
APP_DIR = LOCAL_APPDATA / "ProjectVault"

DATA_DIR = APP_DIR / "data"
LOGS_DIR = APP_DIR / "logs"
BACKUPS_DIR = APP_DIR / "backups"
EXPORTS_DIR = APP_DIR / "exports"

DB_PATH = DATA_DIR / "projectvault.db"

BASE_DIR = Path(__file__).resolve().parent.parent
