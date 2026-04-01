from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


# ── Helpers ─────────────────────────────────────────────────────────────

def _find_vscode_exe() -> str | None:
    """
    Try to locate VS Code.
    Returns full path to executable if found, otherwise None.
    """
    code_cmd = shutil.which("code")
    if code_cmd:
        return code_cmd

    local_appdata = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    candidates = [
        Path(local_appdata) / "Programs" / "Microsoft VS Code" / "Code.exe",
        Path(program_files) / "Microsoft VS Code" / "Code.exe",
        Path(program_files_x86) / "Microsoft VS Code" / "Code.exe",
    ]

    for exe_path in candidates:
        if exe_path.exists():
            return str(exe_path)

    return None


def _safe_path(path: str) -> str:
    return str(Path(path).resolve())


# ── Launch helpers ──────────────────────────────────────────────────────

def open_folder(path: str) -> None:
    os.startfile(_safe_path(path))


def open_in_vscode(path: str) -> None:
    target = _safe_path(path)
    vscode_exe = _find_vscode_exe()

    if not vscode_exe:
        raise FileNotFoundError(
            "VS Code was not found. Install Visual Studio Code or add the "
            "'code' command to your Windows PATH."
        )

    subprocess.Popen([vscode_exe, target], shell=False)


def open_terminal(path: str) -> None:
    """
    Open a brand-new CMD window in front, at the requested folder.
    """
    target = _safe_path(path)
    subprocess.Popen(
        f'start "" cmd.exe /K cd /d "{target}"',
        shell=True,
    )


def open_powershell(path: str) -> None:
    """
    Open a brand-new PowerShell window in front, at the requested folder.
    """
    target = _safe_path(path)
    subprocess.Popen(
        f'start "" powershell.exe -NoExit -Command "Set-Location -LiteralPath \'{target}\'"',
        shell=True,
    )
