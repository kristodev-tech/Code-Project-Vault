import sqlite3
from core.settings import DB_PATH, DATA_DIR


SCHEMA = '''
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    status TEXT DEFAULT 'Planning',
    language TEXT DEFAULT '',
    framework TEXT DEFAULT '',
    category TEXT DEFAULT '',
    tags TEXT DEFAULT '',
    is_favorite INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0,
    created_at TEXT DEFAULT '',
    updated_at TEXT DEFAULT '',
    last_opened_at TEXT DEFAULT '',
    last_scanned_at TEXT DEFAULT '',
    git_enabled INTEGER DEFAULT 0,
    git_branch TEXT DEFAULT '',
    remote_url TEXT DEFAULT '',
    github_repo_name TEXT DEFAULT '',
    github_connected INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_commands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    command TEXT NOT NULL,
    working_dir TEXT DEFAULT '',
    is_default INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS project_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    activity_type TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT NOT NULL
);
'''


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DB] Using database: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[DB] Initializing database: {DB_PATH}")

    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
