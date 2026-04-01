from dataclasses import dataclass, field


@dataclass
class Project:
    id: int | None = None
    name: str = ""
    root_path: str = ""
    description: str = ""
    notes: str = ""
    status: str = "Planning"
    language: str = ""
    framework: str = ""
    category: str = ""
    tags: str = ""
    is_favorite: int = 0
    is_archived: int = 0
    created_at: str = ""
    updated_at: str = ""
    last_opened_at: str = ""
    last_scanned_at: str = ""
    git_enabled: int = 0
    git_branch: str = ""
    remote_url: str = ""
    github_repo_name: str = ""
    github_connected: int = 0


@dataclass
class ScanCandidate:
    path: str
    name: str
    language: str = ""
    framework: str = ""
    git_enabled: int = 0
    git_branch: str = ""
    remote_url: str = ""
    key_files: list[str] = field(default_factory=list)


@dataclass
class ProjectCommand:
    id: int | None = None
    project_id: int = 0
    name: str = ""
    command: str = ""
    working_dir: str = ""
    is_default: int = 0


@dataclass
class ProjectActivity:
    id: int | None = None
    project_id: int = 0
    activity_type: str = ""
    message: str = ""
    created_at: str = ""
