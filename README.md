# Project Vault

**Project Vault** is a Windows desktop application for organizing, launching, inspecting, tracking, and publishing code projects from one place.

It is designed for developers who manage many local projects and want a faster way to browse project folders, view important details, launch tools, store repeatable commands, inspect Git status, and publish projects to GitHub.

**THIS REPO WAS CREATED USING CODE PROJECT VAULT**
---

## Features

### Project Organization
- Add projects manually
- Scan a parent folder for likely projects and import them
- Edit project details
- Mark projects as favorites
- Archive and restore projects
- Delete projects from Project Vault without deleting the actual folder
- Filter projects by:
  - search text
  - tag
  - status
  - category
  - favorites only
  - archived visibility

### Project Table
- Single-click a row to load project details
- Double-click a row to open the project folder
- Click column headers to sort
- Right-click a project row for quick actions:
  - Open Folder
  - Open VS Code
  - Open CMD
  - Open PowerShell
  - Favorite / Unfavorite
  - Archive / Restore
  - Edit Project
  - Re-Scan Project
  - Delete Project

### Launch Tools
- Open Folder in Windows Explorer
- Open project in Visual Studio Code
- Open Command Prompt in the project folder
- Open PowerShell in the project folder

### Saved Commands
- Add saved commands per project
- Edit saved commands
- Delete saved commands
- Run selected saved command
- Run default saved command
- Store working directory with each command
- Keep only one default command per project

### Project Details Panel
- Project type badge detection
- Local Git status and branch details
- Remote URL display
- Last commit information
- Description and notes
- README preview with Markdown rendering
- Key files list
- Saved commands list
- Recently modified files
- Recent project activity

### Activity Tracking
- View recent actions across all projects
- Track project-related operations such as:
  - add project
  - edit project
  - open folder
  - run command
  - re-scan project
  - publish workflow actions

### GitHub Integration
- User-configured GitHub App setup
- GitHub device-flow connection
- Publish selected projects directly to GitHub
- Initialize Git automatically if needed
- Create first commit if needed
- Create GitHub repository
- Add or update remote origin
- Push current branch

### Backup and Restore
- Export project data to JSON
- Import project data from JSON
- Preserve projects, commands, and activity history

### UI / UX
- Dark theme
- Status bar feedback
- Resizable layout
- Better multi-row toolbar layout for smaller screens
- Copyable help documentation
- Markdown README preview

---

## Why Use Project Vault

Project Vault helps reduce the friction of working with many local projects by putting common tasks into one desktop application.

Instead of manually navigating folders, remembering command syntax, opening terminals by hand, and checking Git status from multiple tools, Project Vault centralizes those actions into one interface.

This is especially useful if you:
- maintain many small or medium projects
- frequently switch between Python, React, embedded, C/C++, Android, or other project types
- want to store common build/run/test commands
- want a cleaner way to publish local projects to GitHub
- want local project metadata and notes in one place

---

## Main Screens

## Projects View
The Projects view is the main workspace.

It includes:
- project table
- categories sidebar
- filters
- project details panel
- quick action buttons

## Activity View
The Activity view shows recent actions across all tracked projects.

---

## Supported Project Types

Project Vault can infer a project type badge from project metadata and contents, such as:

- Python
- React
- Android
- Embedded
- AI
- Game
- Node
- TypeScript
- Java
- Rust
- Go
- Ruby
- PHP
- Docker
- SQL
- C
- C++

If no specific type is detected, the project is shown as a general app/project type.

---

## Local Data Storage

Project Vault stores its local data under the current user's local application data directory.

Examples include:

database
logs
backups
exports
GitHub config
GitHub session data

## Typical Workflow

1. Add or import projects
2. Assign categories, tags, notes, and statuses
3. Sort and filter the project list
4. Inspect README, Git info, key files, and activity
5. Save common project commands
6. Launch folders, code editors, terminals, or shells quickly
7. Optionally configure GitHub publishing
8. Export backups periodically

---

## GitHub Publishing Overview

Project Vault supports a user-configured GitHub publishing workflow.

This means:

- Project Vault does **not** ship with a built-in GitHub App Client ID or Slug
- each user provides their **own**
  - GitHub App Client ID
  - GitHub App Slug
- those settings are saved locally on that PC for that user
- the user can then connect GitHub and publish projects directly from Project Vault

---

## GitHub Publishing Workflow in Project Vault

### Step 1 — Create Your GitHub App
Each user must first create or use their own GitHub App.

### Step 2 — Enter GitHub Settings
In Project Vault:
- click **GitHub Settings**
- enter:
  - GitHub App Client ID
  - GitHub App Slug
- click **Save**

### Step 3 — Connect GitHub
- click **Connect GitHub**
- start device sign-in
- approve access in browser
- finish sign-in in the app

### Step 4 — Publish a Project
- select a project
- click **Publish to GitHub**
- choose repository settings
- publish

If the project is not already a Git repository, Project Vault can initialize Git and create the first commit automatically.

---

## How to Create a GitHub App

Go to GitHub:

- **Settings**
- **Developer settings**
- **GitHub Apps**
- **New GitHub App**

### Recommended Registration Settings

#### Basic App Info
- **GitHub App name:** choose a unique name
- **Description:** describe that it is used by your local Project Vault app
- **Homepage URL:** use your website, public repository, or account URL

#### Identifying and Authorizing Users
- **Callback URL:** leave blank for this Project Vault device-flow setup
- **Expire user authorization tokens:** enabled
- **Request user authorization during installation:** off
- **Enable Device Flow:** on

#### Post Installation
- **Setup URL:** leave blank unless you have your own web setup page
- **Redirect on update:** off unless using a Setup URL

#### Webhook
For the current Project Vault workflow:
- **Webhook Active:** off
- **Webhook URL:** blank
- **Secret:** blank

### Recommended Permissions

#### Repository Permissions
- **Contents:** Read and write
- **Metadata:** Read-only
- **Administration:** Read and write

#### Organization Permissions
- No access for now unless needed for your setup

#### Account Permissions
- No access for now unless your workflow requires them later

### Subscribe to Events
- none required for the current Project Vault workflow

### Installation Target
Choose one of:
- **Only on this account** — best for private testing
- **Any account** — best if multiple users should install and use it

---

## After Creating the GitHub App

After you create the GitHub App:

1. copy the **Client ID**
2. find the **Slug**
3. install the app into the GitHub account or organization where you want to publish repositories
4. open Project Vault
5. go to **GitHub Settings**
6. save your Client ID and Slug
7. connect GitHub
8. publish projects

---

## GitHub Publish Behavior

When publishing a project, Project Vault can:

- detect whether the project is already using Git
- initialize Git if needed
- create the first commit if needed
- create a GitHub repository
- add or update `origin`
- push the current branch

---

## Notes About GitHub Configuration

GitHub App settings are:

user-specific
local to that PC
not embedded into the app by default

This means each user can control their own GitHub integration without the app shipping someone else’s GitHub identity or app registration.

## Troubleshooting
GitHub Not Configured

If the app says GitHub is not configured:

open GitHub Settings
enter:
Client ID
App Slug
save
Sign-In Works But No Installations Are Found

Make sure the GitHub App was actually installed into:

your GitHub account, or
the organization where you want to publish
Publish Fails During Commit

Make sure Git is configured on that PC:

git config --global user.name "Your Name"
git config --global user.email "you@example.com"
Publish Fails During Push

Check:

GitHub App permissions
GitHub App installation target
repository creation permissions
account/org installation state
VS Code Launch Fails

Make sure Visual Studio Code is installed and available on that PC.

## Project Not Detected During Scan

Project scanning depends on common project markers and source files.
Some folders may not be detected if they do not contain recognizable markers.

## Important Notes
Deleting a project from Project Vault does not delete the actual folder
Archiving hides projects from the normal active list
GitHub settings and sessions are local to the current user and current PC
Git features depend on Git being installed
VS Code launching depends on VS Code being installed
Future Improvements

## Potential future enhancements may include:

richer GitHub publishing feedback
better organization publishing workflows
enhanced GitHub App validation
Windows Credential Manager integration for GitHub session storage
more project health checks
more export/reporting features
additional command management features

## Project Details Panel

The details panel shows useful project information including:

- type badge
- status
- language
- framework
- category
- tags
- path
- favorite state
- archive state
- last opened time
- last scanned time

### Git Section
The Git section can display:
- Git enabled or not
- current branch
- remote URL
- status summary
- modified files count
- untracked files count
- ahead / behind information
- last commit hash
- last commit message
- last commit author
- last commit date

### README Preview
The README section can:
- locate a README file in the project
- render Markdown when supported
- allow opening the README directly
- allow copying the README path

### Other Lists
The panel also shows:
- key files
- saved commands
- recent modified files
- recent activity

---

## Saved Commands

Saved commands let you store reusable project-specific commands.

Examples:
- build commands
- run commands
- test commands
- deployment scripts
- environment startup commands

Each command can store:
- name
- command string
- working directory
- default state

Only one command per project can be marked as the default command.

---

## Backups

Project Vault supports JSON backup and restore.

### Export Backup
Exports:
- projects
- commands
- activity entries

### Import Backup
Imports:
- projects
- commands
- activity entries

This is useful for:
- migration
- backup
- recovery
- multi-PC setup if desired

---

## Installation and Running

Project Vault is a desktop application built with Python and PySide6.

Typical source dependencies include:
- Python 3
- PySide6
- SQLite (via Python stdlib)
- Git installed on the machine for Git features
- Visual Studio Code installed if you want VS Code launch support

ProjectVault/
├── main.py
├── app.py
├── assets/
│   └── icons/
├── core/
│   ├── db.py
│   ├── scanner.py
│   ├── project_service.py
│   ├── github_auth.py
│   ├── github_publish.py
│   ├── github_config.py
│   └── settings.py
├── ui/
│   ├── main_window.py
│   ├── project_detail_panel.py
│   ├── add_project_dialog.py
│   ├── import_projects_dialog.py
│   ├── command_dialog.py
│   ├── github_app_settings_dialog.py
│   ├── github_connect_dialog.py
│   ├── github_publish_dialog.py
│   ├── help_dialog.py
│   └── widgets/
│       └── project_table.py

### Run From Source
Example:

```bash
python main.py
