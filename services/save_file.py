from pathlib import Path
import re

BASE_SAVE_DIR = Path("/tmp")
BASE_SAVE_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(filename: str) -> str:
    """
    Keep only a safe leaf filename.
    Prevents path traversal like ../../etc/passwd
    """
    name = Path(filename).name.strip()

    if not name:
        raise ValueError("Filename cannot be empty.")

    if not name.endswith(".txt"):
        name += ".txt"

    return name


def save_text_file(filename: str, content: str) -> Path:
    safe_name = sanitize_filename(filename)
    path = BASE_SAVE_DIR / safe_name
    path.write_text(content, encoding="utf-8")
    return path
