from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from core.github_auth import _api_request, get_valid_access_token


class GitHubPublishError(RuntimeError):
    pass


def _git_env() -> dict[str, str]:
    env = os.environ.copy()

    # Prevent Git from waiting for interactive username/password prompts.
    env["GIT_TERMINAL_PROMPT"] = "0"

    # Prevent GUI askpass popups from blocking the worker.
    env["GIT_ASKPASS"] = ""
    env["SSH_ASKPASS"] = ""

    return env


def _run_git(repo_path: Path, args: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            shell=False,
            timeout=120,
            check=False,
            env=_git_env(),
        )
        output = (result.stdout or "").strip()
        err = (result.stderr or "").strip()
        combined = output if output else err
        return result.returncode == 0, combined
    except Exception as exc:
        return False, str(exc)


def is_git_repo(project_path: str) -> bool:
    return (Path(project_path) / ".git").exists()


def ensure_git_repo(project_path: str, default_branch: str = "main") -> None:
    repo = Path(project_path)
    ok, _ = _run_git(repo, ["rev-parse", "--is-inside-work-tree"])
    if ok:
        return

    ok, out = _run_git(repo, ["init", "-b", default_branch])
    if not ok:
        raise GitHubPublishError(f"Failed to initialize Git repository: {out}")


def ensure_initial_commit(project_path: str, commit_message: str) -> None:
    repo = Path(project_path)

    ok, _ = _run_git(repo, ["rev-parse", "--verify", "HEAD"])
    if ok:
        return

    ok, out = _run_git(repo, ["add", "."])
    if not ok:
        raise GitHubPublishError(f"Failed to stage files: {out}")

    ok, out = _run_git(repo, ["commit", "-m", commit_message])
    if not ok:
        raise GitHubPublishError(
            "Failed to create initial commit. Make sure Git user.name and user.email are configured.\n\n"
            f"{out}"
        )


def get_current_branch(project_path: str) -> str:
    repo = Path(project_path)
    ok, out = _run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
    if ok and out:
        return out.strip()
    return "main"


def set_remote_origin(project_path: str, remote_url: str) -> None:
    repo = Path(project_path)

    ok, _ = _run_git(repo, ["remote", "get-url", "origin"])
    if ok:
        ok, out = _run_git(repo, ["remote", "set-url", "origin", remote_url])
        if not ok:
            raise GitHubPublishError(f"Failed to update remote origin: {out}")
        return

    ok, out = _run_git(repo, ["remote", "add", "origin", remote_url])
    if not ok:
        raise GitHubPublishError(f"Failed to add remote origin: {out}")


def _build_authenticated_remote_url(clone_url: str, token: str) -> str:
    parts = urlsplit(clone_url)
    if parts.scheme not in {"http", "https"}:
        raise GitHubPublishError("Only HTTPS clone URLs are supported for GitHub publish.")

    # GitHub App / token-based Git over HTTPS format:
    # https://x-access-token:TOKEN@github.com/owner/repo.git
    netloc = f"x-access-token:{token}@{parts.netloc}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def push_branch(project_path: str, branch: str, authenticated_remote_url: str) -> None:
    repo = Path(project_path)

    # Temporarily push using an authenticated URL so Git never prompts.
    ok, out = _run_git(repo, ["remote", "set-url", "origin", authenticated_remote_url])
    if not ok:
        raise GitHubPublishError(f"Failed to apply authenticated remote for push: {out}")

    ok, out = _run_git(repo, ["push", "-u", "origin", branch])
    if not ok:
        raise GitHubPublishError(f"Failed to push branch '{branch}': {out}")


def create_user_repo(
    repo_name: str,
    description: str = "",
    private: bool = True,
    auto_init: bool = False,
) -> dict[str, Any]:
    token = get_valid_access_token()
    payload = {
        "name": repo_name,
        "description": description,
        "private": private,
        "auto_init": auto_init,
    }
    data = _api_request("POST", "/user/repos", token, payload)
    return data if isinstance(data, dict) else {}


def create_org_repo(
    org: str,
    repo_name: str,
    description: str = "",
    private: bool = True,
) -> dict[str, Any]:
    token = get_valid_access_token()
    payload = {
        "name": repo_name,
        "description": description,
        "private": private,
    }
    data = _api_request("POST", f"/orgs/{org}/repos", token, payload)
    return data if isinstance(data, dict) else {}


def publish_project(
    project_path: str,
    repo_name: str,
    owner_type: str = "user",
    owner_name: str = "",
    description: str = "",
    private: bool = True,
    commit_message: str = "Initial commit",
    init_git_if_needed: bool = True,
) -> dict[str, Any]:
    path = Path(project_path)
    if not path.exists() or not path.is_dir():
        raise GitHubPublishError("Project folder does not exist.")

    if init_git_if_needed:
        ensure_git_repo(project_path)

    ensure_initial_commit(project_path, commit_message)

    if owner_type == "org" and owner_name.strip():
        repo = create_org_repo(
            org=owner_name.strip(),
            repo_name=repo_name,
            description=description,
            private=private,
        )
    else:
        repo = create_user_repo(
            repo_name=repo_name,
            description=description,
            private=private,
            auto_init=False,
        )

    clone_url = str(repo.get("clone_url", "")).strip()
    html_url = str(repo.get("html_url", "")).strip()
    default_branch = get_current_branch(project_path)

    if not clone_url:
        raise GitHubPublishError("GitHub repository was created, but no clone URL was returned.")

    # Save the clean public remote URL in the repo first.
    set_remote_origin(project_path, clone_url)

    # Use the current GitHub user access token for the actual push.
    token = get_valid_access_token()
    authenticated_remote_url = _build_authenticated_remote_url(clone_url, token)

    try:
        push_branch(project_path, default_branch, authenticated_remote_url)
    finally:
        # Always restore the clean remote URL so the token is not left in config.
        try:
            set_remote_origin(project_path, clone_url)
        except Exception:
            pass

    return {
        "repo_name": repo_name,
        "repo_url": html_url,
        "clone_url": clone_url,
        "branch": default_branch,
    }
