from __future__ import annotations

from core.models import Project


def get_project_type_badge(project: Project | None) -> str:
    if not project:
        return "📦 App"

    language = (project.language or "").lower()
    framework = (project.framework or "").lower()
    category = (project.category or "").lower()
    tags = (project.tags or "").lower()
    path_text = (project.root_path or "").lower()
    name_text = (project.name or "").lower()

    combined = f"{language} {framework} {category} {tags} {path_text} {name_text}"

    if any(token in combined for token in [
        "ai", "ml", "llm", "huggingface", "transformer",
        "ollama", "openai", "machine learning"
    ]):
        return "🧠 AI"

    if any(token in combined for token in [
        "game", "unity", "unreal", "godot", "pygame", "three.js", "r3f"
    ]):
        return "🎮 Game"

    if any(token in combined for token in [
        "embedded", "firmware", "xbee", "avr", "stm32",
        "arduino", "serial", "hardware"
    ]):
        return "📡 Embedded"

    if "python" in combined or any(token in combined for token in [
        "pyqt", "pyside", "flask", "django", ".py",
        "pyproject.toml", "requirements.txt"
    ]):
        return "🐍 Py"

    if any(token in combined for token in [
        "next", "react", "vite", "jsx", "tsx"
    ]):
        return "⚛ React"

    if any(token in combined for token in [
        "node", "express", "npm", "package.json"
    ]):
        return "🟩 Node"

    if any(token in combined for token in [
        "typescript", "tsconfig", ".ts"
    ]):
        return "🔷 TS"

    if any(token in combined for token in [
        "android", "kotlin", "gradle", "androidmanifest"
    ]):
        return "🤖 Android"

    if any(token in combined for token in [
        "java", "spring", "maven", "pom.xml"
    ]):
        return "☕ Java"

    if any(token in combined for token in [
        "rust", "cargo.toml"
    ]):
        return "🦀 Rust"

    if any(token in combined for token in [
        "golang", "go ", "go.mod"
    ]):
        return "🐹 Go"

    if any(token in combined for token in [
        "ruby", "rails", "gemfile"
    ]):
        return "💎 Ruby"

    if any(token in combined for token in [
        "php", "laravel", "composer.json"
    ]):
        return "🐘 PHP"

    if any(token in combined for token in [
        "docker", "dockerfile", "docker-compose"
    ]):
        return "🐳 Docker"

    if any(token in combined for token in [
        "sql", "sqlite", "postgres", "mysql", "database"
    ]):
        return "🗄 SQL"

    if any(token in combined for token in [
        "c++", "cpp", ".cpp", ".hpp", ".vcxproj", ".sln", "cmake"
    ]):
        return "🧩 C++"

    if any(token in combined for token in [
        " c ", ".c", ".h", "makefile"
    ]) and "c++" not in combined and "cpp" not in combined:
        return "⚙ C"

    if any(token in combined for token in [
        "html", "css", "web"
    ]):
        return "🌐 Web"

    return "📦 App"