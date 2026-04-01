from pathlib import Path


def safe_name_from_path(path: str) -> str:
    return Path(path).name or path


def normalize_tags(tag_text: str) -> str:
    parts = [part.strip() for part in tag_text.split(",") if part.strip()]
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = part.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(part)
    return ", ".join(deduped)
