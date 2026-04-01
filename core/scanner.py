from __future__ import annotations

import subprocess
from pathlib import Path
import os
from core.models import ScanCandidate
from core.utils import safe_name_from_path

IGNORE_DIRS = {
    ".git", ".next", "node_modules", ".venv", "venv", "dist", "build",
    "__pycache__", ".idea", ".vscode", "coverage", "out", "bin", "obj"
}

PROJECT_MARKERS = {
    "requirements.txt", "pyproject.toml", "setup.py", "package.json", "next.config.js",
    "next.config.ts", "vite.config.js", "vite.config.ts", "CMakeLists.txt", "Makefile",
    "build.gradle", "settings.gradle", "AndroidManifest.xml", ".git", "README.md"
}

SOURCE_HINTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".kt", ".cpp", ".c", ".h", ".hpp", ".cs"
}

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

def _run_git(path: Path, args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            shell=False,
            **_hidden_subprocess_kwargs(),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def _detect_language_and_framework(path: Path) -> tuple[str, str, list[str]]:
    names = {p.name for p in path.iterdir()}
    key_files = sorted(name for name in names if name in PROJECT_MARKERS)

    language = ""
    framework = ""

    if "pyproject.toml" in names or "requirements.txt" in names or "setup.py" in names:
        language = "Python"
    if "package.json" in names:
        language = "JavaScript/TypeScript"
    if "CMakeLists.txt" in names or "Makefile" in names:
        language = language or "C/C++"
    if "build.gradle" in names or "settings.gradle" in names or "AndroidManifest.xml" in names:
        language = language or "Java/Kotlin"
        framework = "Android"

    if "next.config.js" in names or "next.config.ts" in names:
        framework = "Next.js"
    elif "vite.config.js" in names or "vite.config.ts" in names:
        framework = "Vite"

    if not language:
        exts = {p.suffix.lower() for p in path.iterdir() if p.is_file()}
        if ".py" in exts:
            language = "Python"
        elif exts & {".js", ".ts", ".tsx", ".jsx"}:
            language = "JavaScript/TypeScript"
        elif exts & {".cpp", ".c", ".h", ".hpp"}:
            language = "C/C++"
        elif exts & {".java", ".kt"}:
            language = "Java/Kotlin"
        elif ".cs" in exts:
            language = "C#"

    if not framework and (path / "src").exists() and (path / "package.json").exists():
        framework = "Web App"

    return language, framework, key_files


def scan_project_folder(folder: str) -> dict:
    path = Path(folder)
    language, framework, key_files = _detect_language_and_framework(path)
    git_enabled = 1 if (path / ".git").exists() else 0
    git_branch = _run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"]) if git_enabled else ""
    remote_url = _run_git(path, ["remote", "get-url", "origin"]) if git_enabled else ""
    return {
        "language": language,
        "framework": framework,
        "key_files": key_files,
        "git_enabled": git_enabled,
        "git_branch": git_branch,
        "remote_url": remote_url,
    }


def discover_projects(root_folder: str, max_depth: int = 3) -> list[ScanCandidate]:
    root = Path(root_folder)
    found: list[ScanCandidate] = []
    seen: set[Path] = set()

    def walk(path: Path, depth: int) -> None:
        if depth > max_depth or path in seen:
            return
        seen.add(path)
        try:
            children = list(path.iterdir())
        except Exception:
            return

        child_names = {p.name for p in children}
        child_exts = {p.suffix.lower() for p in children if p.is_file()}
        has_marker = bool(child_names & PROJECT_MARKERS)
        has_source = bool(child_exts & SOURCE_HINTS)

        if has_marker or has_source:
            info = scan_project_folder(str(path))
            found.append(
                ScanCandidate(
                    path=str(path),
                    name=safe_name_from_path(str(path)),
                    language=info["language"],
                    framework=info["framework"],
                    git_enabled=info["git_enabled"],
                    git_branch=info["git_branch"],
                    remote_url=info["remote_url"],
                    key_files=info["key_files"],
                )
            )
            return

        for child in children:
            if child.is_dir() and child.name not in IGNORE_DIRS:
                walk(child, depth + 1)

    walk(root, 0)
    found.sort(key=lambda item: item.name.lower())
    return found


def recent_modified_files(folder: str, limit: int = 12) -> list[tuple[str, str]]:
    root = Path(folder)
    if not root.exists() or not root.is_dir():
        return []

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

    entries: list[tuple[float, str]] = []

    try:
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]

            for filename in filenames:
                full_path = Path(current_root) / filename

                try:
                    stat = full_path.stat()
                except Exception:
                    continue

                try:
                    rel = str(full_path.relative_to(root))
                except Exception:
                    continue

                entries.append((stat.st_mtime, rel))
    except Exception:
        return []

    entries.sort(key=lambda item: item[0], reverse=True)

    from datetime import datetime
    return [
        (rel, datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S"))
        for ts, rel in entries[:limit]
    ]


def git_status_snapshot(folder: str) -> dict:
    path = Path(folder)
    if not (path / ".git").exists():
        return {
            "git_enabled": 0,
            "branch": "",
            "remote": "",
            "status_summary": "Git not initialized",
            "modified_count": 0,
            "untracked_count": 0,
            "ahead_behind": "",
        }

    branch = _run_git(path, ["rev-parse", "--abbrev-ref", "HEAD"])
    remote = _run_git(path, ["remote", "get-url", "origin"])
    porcelain = _run_git(path, ["status", "--porcelain"])
    modified_count = 0
    untracked_count = 0
    if porcelain:
        for line in porcelain.splitlines():
            code = (line[:2] or "").strip()
            if code == "??":
                untracked_count += 1
            else:
                modified_count += 1
    ahead_behind = _run_git(path, ["status", "--branch", "--porcelain"])
    ahead_behind_line = ahead_behind.splitlines()[0] if ahead_behind else ""
    summary_bits = []
    if modified_count:
        summary_bits.append(f"modified: {modified_count}")
    if untracked_count:
        summary_bits.append(f"untracked: {untracked_count}")
    status_summary = ", ".join(summary_bits) if summary_bits else "Working tree clean"
    return {
        "git_enabled": 1,
        "branch": branch,
        "remote": remote,
        "status_summary": status_summary,
        "modified_count": modified_count,
        "untracked_count": untracked_count,
        "ahead_behind": ahead_behind_line.replace("##", "").strip(),
    }
