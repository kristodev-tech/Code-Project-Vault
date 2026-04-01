from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

from core.db import get_connection
from core.models import Project, ProjectActivity, ProjectCommand
from core.scanner import git_status_snapshot, recent_modified_files, scan_project_folder


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_activity(project_id: int, activity_type: str, message: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO project_activity (project_id, activity_type, message, created_at) VALUES (?, ?, ?, ?)",
            (project_id, activity_type, message, _now()),
        )
        conn.commit()
    finally:
        conn.close()


def list_projects(
    search_text: str = "",
    tag_filter: str = "All Tags",
    status_filter: str = "All Statuses",
    category_filter: str = "All Categories",
    show_archived: bool = False,
    favorites_only: bool = False,
) -> list[Project]:
    conn = get_connection()
    try:
        where_parts = ["is_archived = ?"]
        params: list[object] = [1 if show_archived else 0]

        if search_text.strip():
            token = f"%{search_text.strip()}%"
            where_parts.append(
                "(name LIKE ? OR tags LIKE ? OR language LIKE ? OR framework LIKE ? OR root_path LIKE ? OR description LIKE ? OR notes LIKE ?)"
            )
            params.extend([token, token, token, token, token, token, token])

        if tag_filter and tag_filter != "All Tags":
            where_parts.append("LOWER(tags) LIKE ?")
            params.append(f"%{tag_filter.lower()}%")

        if status_filter and status_filter != "All Statuses":
            where_parts.append("status = ?")
            params.append(status_filter)

        if category_filter and category_filter != "All Categories":
            where_parts.append("category = ?")
            params.append(category_filter)

        if favorites_only:
            where_parts.append("is_favorite = 1")

        sql = f"""
            SELECT * FROM projects
            WHERE {' AND '.join(where_parts)}
            ORDER BY is_favorite DESC, updated_at DESC, name COLLATE NOCASE
        """
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [Project(**dict(row)) for row in rows]
    finally:
        conn.close()


def dashboard_stats() -> dict:
    conn = get_connection()
    try:
        total = int(conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0])
        active = int(conn.execute("SELECT COUNT(*) FROM projects WHERE is_archived = 0").fetchone()[0])
        archived = int(conn.execute("SELECT COUNT(*) FROM projects WHERE is_archived = 1").fetchone()[0])
        favorites = int(conn.execute("SELECT COUNT(*) FROM projects WHERE is_favorite = 1").fetchone()[0])
        git_enabled = int(conn.execute("SELECT COUNT(*) FROM projects WHERE git_enabled = 1").fetchone()[0])
        return {
            "total": total,
            "active": active,
            "archived": archived,
            "favorites": favorites,
            "git_enabled": git_enabled,
        }
    finally:
        conn.close()


def list_tags() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT tags FROM projects WHERE tags IS NOT NULL AND tags != ''").fetchall()
        found: set[str] = set()
        for row in rows:
            for tag in str(row[0]).split(","):
                tag = tag.strip()
                if tag:
                    found.add(tag)
        return sorted(found, key=str.lower)
    finally:
        conn.close()


def list_statuses() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute("SELECT DISTINCT status FROM projects WHERE status IS NOT NULL AND status != '' ORDER BY status COLLATE NOCASE").fetchall()
        return [str(row[0]) for row in rows]
    finally:
        conn.close()


def list_categories() -> list[str]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT DISTINCT category FROM projects "
            "WHERE category IS NOT NULL AND category != '' "
            "ORDER BY category COLLATE NOCASE"
        ).fetchall()
        return [str(row[0]) for row in rows]
    finally:
        conn.close()


def add_project(project: Project) -> int:
    now = _now()
    conn = get_connection()
    try:
        cur = conn.execute(
            '''
            INSERT INTO projects (
                name, root_path, description, notes, status, language, framework, category, tags,
                is_favorite, is_archived, created_at, updated_at, last_opened_at, last_scanned_at,
                git_enabled, git_branch, remote_url, github_repo_name, github_connected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                project.name, project.root_path, project.description, project.notes, project.status,
                project.language, project.framework, project.category, project.tags,
                project.is_favorite, project.is_archived, now, now, project.last_opened_at, project.last_scanned_at,
                project.git_enabled, project.git_branch, project.remote_url,
                project.github_repo_name, project.github_connected,
            ),
        )
        conn.commit()
        project_id = int(cur.lastrowid)
    finally:
        conn.close()
    log_activity(project_id, "project", f"Project added: {project.name}")
    return project_id


def get_project(project_id: int) -> Project | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return Project(**dict(row)) if row else None
    finally:
        conn.close()


def project_exists(root_path: str) -> bool:
    conn = get_connection()
    try:
        row = conn.execute("SELECT 1 FROM projects WHERE root_path = ?", (root_path,)).fetchone()
        return row is not None
    finally:
        conn.close()


def update_project(project: Project) -> None:
    if project.id is None:
        raise ValueError("Project id is required for update.")
    conn = get_connection()
    try:
        conn.execute(
            '''
            UPDATE projects
            SET name = ?, root_path = ?, description = ?, notes = ?, status = ?, language = ?, framework = ?,
                category = ?, tags = ?, is_favorite = ?, is_archived = ?, updated_at = ?, last_scanned_at = ?,
                git_enabled = ?, git_branch = ?, remote_url = ?, github_repo_name = ?, github_connected = ?
            WHERE id = ?
            ''',
            (
                project.name, project.root_path, project.description, project.notes, project.status,
                project.language, project.framework, project.category, project.tags, project.is_favorite,
                project.is_archived, _now(), project.last_scanned_at, project.git_enabled, project.git_branch,
                project.remote_url, project.github_repo_name, project.github_connected, project.id,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    log_activity(project.id, "project", f"Project updated: {project.name}")


def delete_project(project_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM project_commands WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM project_activity WHERE project_id = ?", (project_id,))
        conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        conn.commit()
    finally:
        conn.close()


def set_archived(project_id: int, archived: bool) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE projects SET is_archived = ?, updated_at = ? WHERE id = ?",
            (1 if archived else 0, _now(), project_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_activity(project_id, "status", "Archived" if archived else "Restored from archive")


def toggle_favorite(project_id: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT is_favorite FROM projects WHERE id = ?", (project_id,)).fetchone()
        if not row:
            return
        new_value = 0 if int(row[0]) else 1
        conn.execute(
            "UPDATE projects SET is_favorite = ?, updated_at = ? WHERE id = ?",
            (new_value, _now(), project_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_activity(project_id, "favorite", "Marked as favorite" if new_value else "Removed from favorites")


def update_last_opened(project_id: int) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE projects SET last_opened_at = ?, updated_at = ? WHERE id = ?",
            (_now(), _now(), project_id),
        )
        conn.commit()
    finally:
        conn.close()
    log_activity(project_id, "open", "Project opened")


def import_projects(projects: list[Project]) -> tuple[int, int]:
    added = 0
    skipped = 0
    for project in projects:
        normalized = str(Path(project.root_path))
        if project_exists(normalized):
            skipped += 1
            continue
        project.root_path = normalized
        add_project(project)
        added += 1
    return added, skipped


def list_project_commands(project_id: int) -> list[ProjectCommand]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM project_commands WHERE project_id = ? ORDER BY is_default DESC, name COLLATE NOCASE",
            (project_id,),
        ).fetchall()
        return [ProjectCommand(**dict(row)) for row in rows]
    finally:
        conn.close()


def get_project_command(command_id: int) -> ProjectCommand | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM project_commands WHERE id = ?", (command_id,)).fetchone()
        return ProjectCommand(**dict(row)) if row else None
    finally:
        conn.close()


def add_project_command(project_id: int, name: str, command: str, working_dir: str = "", is_default: bool = False) -> int:
    conn = get_connection()
    try:
        if is_default:
            conn.execute("UPDATE project_commands SET is_default = 0 WHERE project_id = ?", (project_id,))
        cur = conn.execute(
            "INSERT INTO project_commands (project_id, name, command, working_dir, is_default) VALUES (?, ?, ?, ?, ?)",
            (project_id, name, command, working_dir, 1 if is_default else 0),
        )
        conn.commit()
        command_id = int(cur.lastrowid)
    finally:
        conn.close()
    log_activity(project_id, "command", f"Command added: {name}")
    return command_id


def update_project_command(
    command_id: int,
    name: str,
    command: str,
    working_dir: str = "",
    is_default: bool = False,
) -> None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT project_id, name FROM project_commands WHERE id = ?",
            (command_id,),
        ).fetchone()
        if not row:
            raise ValueError("Saved command not found.")

        project_id = int(row["project_id"])
        old_name = str(row["name"])

        if is_default:
            conn.execute(
                "UPDATE project_commands SET is_default = 0 WHERE project_id = ?",
                (project_id,),
            )

        conn.execute(
            """
            UPDATE project_commands
            SET name = ?, command = ?, working_dir = ?, is_default = ?
            WHERE id = ?
            """,
            (name, command, working_dir, 1 if is_default else 0, command_id),
        )
        conn.commit()
    finally:
        conn.close()

    if old_name == name:
        log_activity(project_id, "command", f"Command updated: {name}")
    else:
        log_activity(project_id, "command", f"Command updated: {old_name} → {name}")


def delete_project_command(command_id: int) -> None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT project_id, name FROM project_commands WHERE id = ?", (command_id,)).fetchone()
        if not row:
            return
        conn.execute("DELETE FROM project_commands WHERE id = ?", (command_id,))
        conn.commit()
        project_id = int(row["project_id"])
        name = str(row["name"])
    finally:
        conn.close()
    log_activity(project_id, "command", f"Command removed: {name}")


def list_project_activity(project_id: int, limit: int = 25) -> list[ProjectActivity]:
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM project_activity WHERE project_id = ? ORDER BY id DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()
        return [ProjectActivity(**dict(row)) for row in rows]
    finally:
        conn.close()


def list_all_activity(limit: int = 200) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT
                a.id,
                a.project_id,
                p.name AS project_name,
                a.activity_type,
                a.message,
                a.created_at
            FROM project_activity a
            LEFT JOIN projects p ON p.id = a.project_id
            ORDER BY a.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def run_saved_command(command_id: int) -> tuple[bool, str]:
    import os
    import subprocess
    import tempfile
    from pathlib import Path

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM project_commands WHERE id = ?", (command_id,)).fetchone()
        if not row:
            return False, "Command not found."
        cmd = ProjectCommand(**dict(row))
    finally:
        conn.close()

    working_dir = (cmd.working_dir or "").strip()
    if not working_dir:
        project = get_project(cmd.project_id)
        if project:
            working_dir = project.root_path

    command_line = (cmd.command or "").strip()
    if not command_line:
        return False, "Saved command is empty."

    try:
        cwd_path = str(Path(working_dir).resolve()) if working_dir else ""

        if os.name == "nt":
            lines = ["@echo off"]
            if cwd_path:
                lines.append(f'cd /d "{cwd_path}"')
            lines.append(command_line)

            temp_dir = Path(tempfile.gettempdir()) / "ProjectVault"
            temp_dir.mkdir(parents=True, exist_ok=True)

            safe_name = "".join(
                ch if ch.isalnum() or ch in ("-", "_") else "_"
                for ch in (cmd.name or "command")
            )
            script_path = temp_dir / f"run_{cmd.id}_{safe_name}.cmd"
            script_path.write_text("\n".join(lines), encoding="utf-8")

            subprocess.Popen(
                ["cmd.exe", "/K", str(script_path)],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                shell=False,
            )
        else:
            subprocess.Popen(
                command_line,
                cwd=cwd_path or None,
                shell=True,
            )

        log_activity(cmd.project_id, "command", f"Command started: {cmd.name}")
        return True, f"Started: {cmd.name}"

    except Exception as exc:
        return False, str(exc)


def rescan_project(project_id: int) -> None:
    project = get_project(project_id)
    if not project:
        raise ValueError("Project not found.")
    info = scan_project_folder(project.root_path)
    project.language = info["language"]
    project.framework = info["framework"]
    project.git_enabled = info["git_enabled"]
    project.git_branch = info["git_branch"]
    project.remote_url = info["remote_url"]
    project.last_scanned_at = _now()
    update_project(project)
    log_activity(project_id, "scan", "Project re-scanned")


def get_project_recent_files(project_id: int, limit: int = 12) -> list[tuple[str, str]]:
    project = get_project(project_id)
    if not project:
        return []
    return recent_modified_files(project.root_path, limit=limit)


def _hidden_subprocess_kwargs() -> dict:
    """
    Suppress Windows console flashes for background subprocesses.
    """
    if os.name != "nt":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    return {
        "startupinfo": startupinfo,
        "creationflags": subprocess.CREATE_NO_WINDOW,
    }


def get_git_commit_info(root_path: str) -> dict:
    """
    Return last commit details for a Git repo.
    Safe fallback values are returned if Git is unavailable or the folder
    is not a valid repository.
    """
    base = {
        "last_commit_hash": "",
        "last_commit_short_hash": "",
        "last_commit_message": "",
        "last_commit_author": "",
        "last_commit_date": "",
    }

    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                root_path,
                "log",
                "-1",
                "--pretty=format:%H%n%h%n%s%n%an%n%ad",
                "--date=short",
            ],
            capture_output=True,
            text=True,
            shell=False,
            timeout=5,
            **_hidden_subprocess_kwargs(),
        )

        if result.returncode != 0:
            return base

        lines = [line.strip() for line in result.stdout.splitlines()]
        while len(lines) < 5:
            lines.append("")

        base["last_commit_hash"] = lines[0]
        base["last_commit_short_hash"] = lines[1]
        base["last_commit_message"] = lines[2]
        base["last_commit_author"] = lines[3]
        base["last_commit_date"] = lines[4]
        return base

    except Exception:
        return base


def get_project_git_snapshot(project_id: int) -> dict:
    project = get_project(project_id)
    if not project:
        return {
            "git_enabled": 0,
            "branch": "",
            "remote": "",
            "status_summary": "Project not found",
            "modified_count": 0,
            "untracked_count": 0,
            "ahead_behind": "",
            "last_commit_hash": "",
            "last_commit_short_hash": "",
            "last_commit_message": "",
            "last_commit_author": "",
            "last_commit_date": "",
        }

    snapshot = git_status_snapshot(project.root_path)

    if not snapshot.get("git_enabled"):
        snapshot.setdefault("last_commit_hash", "")
        snapshot.setdefault("last_commit_short_hash", "")
        snapshot.setdefault("last_commit_message", "")
        snapshot.setdefault("last_commit_author", "")
        snapshot.setdefault("last_commit_date", "")
        return snapshot

    commit_info = get_git_commit_info(project.root_path)
    snapshot.update(commit_info)
    return snapshot


def export_backup_json(file_path: str) -> tuple[int, int, int]:
    conn = get_connection()
    try:
        projects = [dict(row) for row in conn.execute("SELECT * FROM projects ORDER BY id").fetchall()]
        commands = [dict(row) for row in conn.execute("SELECT * FROM project_commands ORDER BY id").fetchall()]
        activity = [dict(row) for row in conn.execute("SELECT * FROM project_activity ORDER BY id").fetchall()]
    finally:
        conn.close()

    payload = {
        "app": "Project Vault",
        "version": "phase4",
        "exported_at": _now(),
        "projects": projects,
        "commands": commands,
        "activity": activity,
    }
    Path(file_path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return len(projects), len(commands), len(activity)


def import_backup_json(file_path: str) -> tuple[int, int, int]:
    payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
    projects = payload.get("projects", [])
    commands = payload.get("commands", [])
    activity = payload.get("activity", [])

    path_to_new_id: dict[str, int] = {}
    added_projects = 0
    added_commands = 0
    added_activity = 0

    conn = get_connection()
    try:
        for item in projects:
            root_path = str(item.get("root_path", "")).strip()
            if not root_path:
                continue
            existing = conn.execute("SELECT id FROM projects WHERE root_path = ?", (root_path,)).fetchone()
            if existing:
                path_to_new_id[root_path] = int(existing["id"])
                continue
            cur = conn.execute(
                '''
                INSERT INTO projects (
                    name, root_path, description, notes, status, language, framework, category, tags,
                    is_favorite, is_archived, created_at, updated_at, last_opened_at, last_scanned_at,
                    git_enabled, git_branch, remote_url, github_repo_name, github_connected
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    item.get("name", ""), root_path, item.get("description", ""), item.get("notes", ""),
                    item.get("status", "Planning"), item.get("language", ""), item.get("framework", ""),
                    item.get("category", ""), item.get("tags", ""), int(item.get("is_favorite", 0)),
                    int(item.get("is_archived", 0)), item.get("created_at", _now()), item.get("updated_at", _now()),
                    item.get("last_opened_at", ""), item.get("last_scanned_at", ""), int(item.get("git_enabled", 0)),
                    item.get("git_branch", ""), item.get("remote_url", ""), item.get("github_repo_name", ""),
                    int(item.get("github_connected", 0)),
                ),
            )
            new_id = int(cur.lastrowid)
            path_to_new_id[root_path] = new_id
            added_projects += 1

        legacy_id_to_path = {
            int(item.get("id", 0)): str(item.get("root_path", "")).strip()
            for item in projects
            if item.get("id") is not None
        }

        for item in commands:
            old_project_id = int(item.get("project_id", 0))
            root_path = legacy_id_to_path.get(old_project_id, "")
            new_project_id = path_to_new_id.get(root_path)
            if not new_project_id:
                continue
            existing = conn.execute(
                "SELECT 1 FROM project_commands WHERE project_id = ? AND name = ? AND command = ?",
                (new_project_id, item.get("name", ""), item.get("command", "")),
            ).fetchone()
            if existing:
                continue
            conn.execute(
                "INSERT INTO project_commands (project_id, name, command, working_dir, is_default) VALUES (?, ?, ?, ?, ?)",
                (new_project_id, item.get("name", ""), item.get("command", ""), item.get("working_dir", ""), int(item.get("is_default", 0))),
            )
            added_commands += 1

        for item in activity:
            old_project_id = int(item.get("project_id", 0))
            root_path = legacy_id_to_path.get(old_project_id, "")
            new_project_id = path_to_new_id.get(root_path)
            if not new_project_id:
                continue
            conn.execute(
                "INSERT INTO project_activity (project_id, activity_type, message, created_at) VALUES (?, ?, ?, ?)",
                (new_project_id, item.get("activity_type", ""), item.get("message", ""), item.get("created_at", _now())),
            )
            added_activity += 1

        conn.commit()
    finally:
        conn.close()

    return added_projects, added_commands, added_activity


# ── README helpers ────────────────────────────────────────────────────────────

def find_readme_file(root_path: str) -> str:
    """
    Return the full path to the first README file found in the project root.
    """
    root = Path(root_path)
    if not root.exists() or not root.is_dir():
        return ""

    candidates = [
        "README.md",
        "readme.md",
        "README.txt",
        "readme.txt",
    ]

    for name in candidates:
        candidate = root / name
        if candidate.exists() and candidate.is_file():
            return str(candidate)

    return ""


def get_project_readme_path(project_id: int) -> str:
    project = get_project(project_id)
    if not project:
        return ""
    return find_readme_file(project.root_path)


def get_project_readme_text(project_id: int, max_chars: int = 20000) -> str:
    """
    Load README text for preview.
    Limits size so the UI stays responsive.
    """
    readme_path = get_project_readme_path(project_id)
    if not readme_path:
        return ""

    try:
        text = Path(readme_path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = Path(readme_path).read_text(encoding="utf-8", errors="replace")
        except Exception:
            return ""
    except Exception:
        return ""

    text = text.strip()
    if not text:
        return ""

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[README preview truncated]"

    return text


# ── Key file helpers ──────────────────────────────────────────────────────────

def get_project_key_files(project_id: int, limit: int = 50) -> list[tuple[str, str]]:
    """
    Return important project files as a list of:
    (display_name, full_path)

    Optimized to avoid expensive recursion through large generated folders.
    """
    project = get_project(project_id)
    if not project:
        return []

    root = Path(project.root_path)
    if not root.exists() or not root.is_dir():
        return []

    key_names = {
        "main.py",
        "app.py",
        "run.py",
        "manage.py",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "next.config.js",
        "next.config.ts",
        "vite.config.js",
        "vite.config.ts",
        "CMakeLists.txt",
        "Makefile",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "AndroidManifest.xml",
        "README.md",
        "readme.md",
        "README.txt",
        "readme.txt",
        ".env",
        ".env.example",
        ".gitignore",
        "dockerfile",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "composer.json",
        "Gemfile",
        "go.mod",
        "Cargo.toml",
        "pom.xml",
    }

    skip_dirs = {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".next",
        "target",
        "out",
        ".idea",
        ".vs",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
    }

    search_roots = [root]
    for sub in ["src", "app", "frontend", "backend", "android", "server", "client"]:
        subdir = root / sub
        if subdir.exists() and subdir.is_dir():
            search_roots.append(subdir)

    found: list[tuple[str, str]] = []
    seen: set[str] = set()

    for search_root in search_roots:
        for current_root, dirnames, filenames in os.walk(search_root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]

            for filename in filenames:
                if filename in key_names:
                    full_path = Path(current_root) / filename
                    rel_path = str(full_path.relative_to(root))

                    if rel_path not in seen:
                        seen.add(rel_path)
                        found.append((rel_path, str(full_path)))

                        if len(found) >= limit:
                            found.sort(key=lambda item: item[0].lower())
                            return found[:limit]

    found.sort(key=lambda item: item[0].lower())
    return found[:limit]


# ── Optional service wrapper for UI classes ──────────────────────────────────

class ProjectService:
    """
    Thin wrapper around the existing function-based project service API.
    This lets UI code use self.service.record_activity(...), etc.
    """

    def record_activity(self, project_id: int, activity_type: str, message: str) -> None:
        log_activity(project_id, activity_type, message)

    def touch_last_opened(self, project_id: int) -> None:
        update_last_opened(project_id)

    def get_project(self, project_id: int) -> Project | None:
        return get_project(project_id)

    def list_projects(
        self,
        search_text: str = "",
        tag_filter: str = "All Tags",
        status_filter: str = "All Statuses",
        category_filter: str = "All Categories",
        show_archived: bool = False,
        favorites_only: bool = False,
    ) -> list[Project]:
        return list_projects(
            search_text=search_text,
            tag_filter=tag_filter,
            status_filter=status_filter,
            category_filter=category_filter,
            show_archived=show_archived,
            favorites_only=favorites_only,
        )

    def add_project(self, project: Project) -> int:
        return add_project(project)

    def list_categories(self) -> list[str]:
        return list_categories()

    def list_all_activity(self, limit: int = 200) -> list[dict]:
        return list_all_activity(limit=limit)

    def update_project(self, project: Project) -> None:
        update_project(project)

    def delete_project(self, project_id: int) -> None:
        delete_project(project_id)

    def toggle_favorite(self, project_id: int) -> None:
        toggle_favorite(project_id)

    def set_archived(self, project_id: int, archived: bool) -> None:
        set_archived(project_id, archived)

    def list_project_commands(self, project_id: int) -> list[ProjectCommand]:
        return list_project_commands(project_id)

    def get_project_command(self, command_id: int) -> ProjectCommand | None:
        return get_project_command(command_id)

    def add_project_command(
        self,
        project_id: int,
        name: str,
        command: str,
        working_dir: str = "",
        is_default: bool = False,
    ) -> int:
        return add_project_command(project_id, name, command, working_dir, is_default)

    def update_project_command(
        self,
        command_id: int,
        name: str,
        command: str,
        working_dir: str = "",
        is_default: bool = False,
    ) -> None:
        update_project_command(command_id, name, command, working_dir, is_default)

    def delete_project_command(self, command_id: int) -> None:
        delete_project_command(command_id)

    def run_saved_command(self, command_id: int) -> tuple[bool, str]:
        return run_saved_command(command_id)

    def rescan_project(self, project_id: int) -> None:
        rescan_project(project_id)

    def get_recent_files(self, project_id: int, limit: int = 12) -> list[tuple[str, str]]:
        return get_project_recent_files(project_id, limit=limit)

    def get_git_snapshot(self, project_id: int) -> dict:
        return get_project_git_snapshot(project_id)

    def get_readme_path(self, project_id: int) -> str:
        return get_project_readme_path(project_id)

    def get_readme_text(self, project_id: int, max_chars: int = 20000) -> str:
        return get_project_readme_text(project_id, max_chars=max_chars)

    def get_key_files(self, project_id: int, limit: int = 50) -> list[tuple[str, str]]:
        return get_project_key_files(project_id, limit=limit)