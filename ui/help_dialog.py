from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QHBoxLayout,
)


HELP_HTML = """
<h2>Project Vault Help</h2>

<p><b>Project Vault</b> helps you organize, launch, inspect, track, and publish your code projects from one place.</p>

<h3>Overview</h3>
<ul>
  <li><b>Projects view</b> shows your project list and the project details panel.</li>
  <li><b>Activity view</b> shows recent actions across all projects.</li>
  <li><b>Categories sidebar</b> filters projects by category.</li>
  <li><b>Search / Tag / Status filters</b> help narrow down the project list.</li>
  <li><b>Status bar</b> at the bottom shows quick feedback for actions and the currently selected project.</li>
</ul>

<h3>Main Actions</h3>
<ul>
  <li><b>Add Project</b> manually add a project folder.</li>
  <li><b>Scan Parent Folder</b> search a larger folder for likely projects and import them.</li>
  <li><b>Edit</b> update project details.</li>
  <li><b>Favorite</b> mark important projects with a star.</li>
  <li><b>Archive / Restore</b> hide older projects without deleting them.</li>
  <li><b>Delete</b> remove a project from Project Vault's database only.</li>
</ul>

<h3>Working with the Project Table</h3>
<ul>
  <li><b>Single-click</b> a project row to load its details.</li>
  <li><b>Double-click</b> a project row to open that project's folder.</li>
  <li><b>Click a column header</b> to sort by that column. Click again to reverse the sort order.</li>
  <li><b>Right-click a project row</b> to open a context menu with quick actions.</li>
</ul>

<h3>Project Right-Click Menu</h3>
<ul>
  <li><b>Open Folder</b></li>
  <li><b>Open VS Code</b></li>
  <li><b>Open CMD</b></li>
  <li><b>Open PowerShell</b></li>
  <li><b>Mark Favorite / Remove Favorite</b></li>
  <li><b>Archive / Restore</b></li>
  <li><b>Edit Project</b></li>
  <li><b>Re-Scan Project</b></li>
  <li><b>Delete Project</b></li>
</ul>

<h3>Launch Tools</h3>
<ul>
  <li><b>Open Folder</b> opens the project folder in Windows Explorer.</li>
  <li><b>Open VS Code</b> opens the project in Visual Studio Code.</li>
  <li><b>Open CMD</b> opens a new Command Prompt in that project folder.</li>
  <li><b>Open PowerShell</b> opens a new PowerShell window in that project folder.</li>
</ul>

<h3>Saved Commands</h3>
<ul>
  <li><b>Add Command</b> saves a custom command for the selected project.</li>
  <li><b>Edit Selected Command</b> updates the selected saved command.</li>
  <li><b>Run Selected Command</b> runs the command currently selected in the dropdown.</li>
  <li><b>Run Default Command</b> runs the default saved command for that project. If no default is set, the first saved command is used.</li>
  <li><b>Delete Selected Command</b> removes the currently selected saved command.</li>
  <li>Only <b>one saved command</b> per project can be marked as <b>default</b>.</li>
</ul>

<h3>Command Window Behavior</h3>
<ul>
  <li>Saved commands run in a visible command window.</li>
  <li>On Windows, the command window stays open after the command runs.</li>
  <li>The command window opens in the saved working directory, or the project folder if no working directory is set.</li>
</ul>

<h3>Project Details Panel</h3>
<ul>
  <li><b>Type badge</b> shows a detected project type such as Python, React, Android, Embedded, AI, Game, and more.</li>
  <li><b>Git section</b> shows local Git status, branch, remote, and recent commit details.</li>
  <li><b>Description / Notes</b> help document the project.</li>
  <li><b>README Preview</b> displays README text and renders Markdown when possible.</li>
  <li><b>Key Files</b> shows important files and opens them on double-click.</li>
  <li><b>Saved Commands</b> lists commands stored for the selected project.</li>
  <li><b>Recent Modified Files</b> shows recently changed files in the project.</li>
  <li><b>Recent Activity</b> shows recent logged actions for the selected project.</li>
</ul>

<h3>README Preview</h3>
<ul>
  <li><b>Open README</b> opens the README in your default editor or viewer.</li>
  <li><b>Copy README Path</b> copies the full README path to the clipboard.</li>
  <li>Markdown README files are rendered in the preview when supported.</li>
</ul>

<h3>Git Information</h3>
<ul>
  <li>Git data is local and depends on Git being installed on the PC.</li>
  <li>The Git section may show branch, remote, status summary, modified count, untracked count, ahead/behind, and last commit details.</li>
  <li>If a project is not a Git repository, Git fields will show fallback values.</li>
</ul>

<h3>GitHub Features</h3>
<ul>
  <li><b>GitHub Settings</b> lets you enter your GitHub App Client ID and App Slug.</li>
  <li><b>Connect GitHub</b> starts GitHub device sign-in for the current user.</li>
  <li><b>Publish to GitHub</b> creates a repository on GitHub and pushes the selected project.</li>
</ul>

<h3>Important GitHub Design Notes</h3>
<ul>
  <li>Project Vault does <b>not</b> ship with a built-in GitHub App Client ID or Slug.</li>
  <li>Each user must provide their <b>own</b> GitHub App Client ID and App Slug in <b>GitHub Settings</b>.</li>
  <li>GitHub settings are stored <b>locally on that PC</b> for the current user.</li>
  <li>If GitHub settings are cleared, the saved GitHub login session is also removed.</li>
</ul>

<h3>How to Create Your GitHub App</h3>
<ol>
  <li>Sign in to GitHub.</li>
  <li>Go to <b>Settings</b>.</li>
  <li>Open <b>Developer settings</b>.</li>
  <li>Click <b>GitHub Apps</b>.</li>
  <li>Click <b>New GitHub App</b>.</li>
</ol>

<h3>Recommended GitHub App Registration Settings</h3>
<ul>
  <li><b>GitHub App name:</b> choose a unique name. GitHub App names must be unique across GitHub.</li>
  <li><b>Description:</b> describe that the app is used by your local Project Vault desktop application.</li>
  <li><b>Homepage URL:</b> use your public repository URL, website, or account URL.</li>
  <li><b>Callback URL:</b> leave blank for this Project Vault device-flow setup. Callback URLs are ignored when using device flow.</li>
  <li><b>Expire user authorization tokens:</b> leave enabled. This is recommended so GitHub can issue refresh tokens.</li>
  <li><b>Request user authorization during installation:</b> leave off for this setup.</li>
  <li><b>Enable Device Flow:</b> turn this on. Project Vault uses device flow for desktop sign-in.</li>
  <li><b>Setup URL:</b> leave blank unless you have your own post-install setup page.</li>
  <li><b>Redirect on update:</b> leave off unless you are using a Setup URL.</li>
</ul>

<h3>Webhook Setup</h3>
<ul>
  <li>For the current Project Vault workflow, you can turn <b>Webhook Active</b> off.</li>
  <li>If your app is only being used for authentication and publishing from the desktop app, you do not need webhook delivery.</li>
  <li>If webhooks are disabled, you do not need a Webhook URL or Secret.</li>
</ul>

<h3>Recommended Permission Setup</h3>
<p>Choose the <b>minimum permissions necessary</b>. For the current Project Vault publish workflow, the following is the recommended starting setup:</p>
<ul>
  <li><b>Repository permissions</b></li>
  <ul>
    <li><b>Contents:</b> Read and write</li>
    <li><b>Metadata:</b> Read-only</li>
    <li><b>Administration:</b> Read and write</li>
  </ul>
  <li><b>Organization permissions:</b> No access for now unless you specifically need organization-level features.</li>
  <li><b>Account permissions:</b> No access for now unless your specific GitHub App workflow requires them later.</li>
</ul>

<h3>Subscribe to Events</h3>
<ul>
  <li>For the current Project Vault workflow, you can leave <b>Subscribe to events</b> empty.</li>
  <li>Event subscriptions are only needed if you want your GitHub App to receive webhooks and respond to GitHub-side events.</li>
</ul>

<h3>Where Can This GitHub App Be Installed?</h3>
<ul>
  <li><b>Only on this account</b> is best while you are privately testing your own setup.</li>
  <li><b>Any account</b> is best if you want other users to install and use their own copy of the GitHub App configuration.</li>
</ul>

<h3>After You Click Create GitHub App</h3>
<ol>
  <li>Open the new GitHub App settings page.</li>
  <li>Copy the <b>Client ID</b>.</li>
  <li>Find the app <b>Slug</b> from the GitHub App settings page or the app URL.</li>
  <li>Install the GitHub App into the GitHub account or organization where you want to publish repositories.</li>
</ol>

<h3>How to Use That in Project Vault</h3>
<ol>
  <li>Open <b>GitHub Settings</b> in Project Vault.</li>
  <li>Paste in your <b>GitHub App Client ID</b>.</li>
  <li>Paste in your <b>GitHub App Slug</b>.</li>
  <li>Click <b>Save</b>.</li>
  <li>Click <b>Connect GitHub</b>.</li>
  <li>Click <b>Start Sign-In</b>.</li>
  <li>Your browser will open GitHub's device login page.</li>
  <li>Enter the device code shown by Project Vault.</li>
  <li>Approve access.</li>
  <li>Return to Project Vault and click <b>Finish Sign-In</b>.</li>
</ol>

<h3>Publishing Workflow</h3>
<ul>
  <li>Select the project you want to publish.</li>
  <li>Click <b>Publish to GitHub</b>.</li>
  <li>Choose whether to publish to your own account or to an organization.</li>
  <li>Enter the repository name, description, visibility, and commit message.</li>
  <li>If the project is not already using Git, Project Vault can initialize Git first.</li>
  <li>If the project has no commit yet, Project Vault can create the first commit.</li>
  <li>Project Vault then creates the repository on GitHub, adds or updates <b>origin</b>, and pushes the current branch.</li>
</ul>

<h3>GitHub Troubleshooting</h3>
<ul>
  <li>If <b>Connect GitHub</b> says GitHub is not configured, open <b>GitHub Settings</b> and enter your Client ID and Slug first.</li>
  <li>If sign-in works but no installations are found, install your GitHub App into your GitHub account or organization.</li>
  <li>If publishing fails during commit creation, make sure Git has a configured <b>user.name</b> and <b>user.email</b> on that PC.</li>
  <li>If publishing fails during push, verify that the GitHub App has the required permissions and is installed where you are trying to publish.</li>
  <li>If you change your Client ID or Slug, reconnect GitHub afterward so the new settings are used.</li>
</ul>

<h3>Activity View</h3>
<ul>
  <li>Use the <b>Activity</b> view in the left sidebar to review recent actions across projects.</li>
  <li>Actions such as adding projects, editing projects, running commands, rescanning, opening projects, and publishing may appear in activity history.</li>
</ul>

<h3>Backups</h3>
<ul>
  <li><b>Export Backup</b> saves project data to a JSON file.</li>
  <li><b>Import Backup</b> restores project data from a JSON backup.</li>
  <li>Backups can include projects, saved commands, and activity history.</li>
</ul>

<h3>Important Notes</h3>
<ul>
  <li>Deleting a project removes it from Project Vault only. It does <b>not</b> delete the actual project folder.</li>
  <li>Archiving a project hides it from the normal active list until <b>Show Archived</b> is enabled or the project is restored.</li>
  <li>If VS Code launching fails, make sure VS Code is installed and available to the app.</li>
  <li>Project detection during folder scanning is based on common project markers and source files. Some folders may not be detected if they do not contain recognizable markers.</li>
  <li>GitHub settings and sessions are local to the current user on the current PC unless you configure them again elsewhere.</li>
</ul>

<h3>Suggested Workflow</h3>
<ol>
  <li>Add or import your projects.</li>
  <li>Assign categories, tags, notes, and statuses.</li>
  <li>Use sorting, filters, and categories to quickly find projects.</li>
  <li>Use the detail panel to inspect README, Git info, key files, and activity.</li>
  <li>Save common commands for build, run, test, deployment, or other project tasks.</li>
  <li>Use the right-click menu and double-click shortcuts for faster navigation.</li>
  <li>If you want GitHub publishing, create your GitHub App, configure GitHub Settings, connect GitHub, and publish.</li>
  <li>Export backups periodically.</li>
</ol>
"""


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Vault Help")
        self.resize(980, 760)

        layout = QVBoxLayout(self)

        title = QLabel("Project Vault Help")
        title.setStyleSheet("font-size: 20px; font-weight: bold;")

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setOpenLinks(True)
        self.browser.setHtml(HELP_HTML)
        self.browser.setTextInteractionFlags(
            Qt.TextBrowserInteraction | Qt.TextSelectableByMouse
        )

        button_row = QHBoxLayout()
        button_row.addStretch(1)

        copy_btn = QPushButton("Copy Help Text")
        copy_btn.clicked.connect(self.copy_help_text)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        button_row.addWidget(copy_btn)
        button_row.addWidget(close_btn)

        layout.addWidget(title)
        layout.addWidget(self.browser, 1)
        layout.addLayout(button_row)

    def copy_help_text(self) -> None:
        text = self.browser.toPlainText().strip()
        QApplication.clipboard().setText(text)