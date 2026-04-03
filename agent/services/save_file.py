from pathlib import Path
import re

BASE_SAVE_DIR = Path("/tmp/agent007")
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


def try_handle_file_create(message: str):
    """
    Very simple command parser.

    Supported examples:
    - create a text file called notes.txt with this context: hello world
    - save a text file named summary with this context: abc
    - write file todo.txt: buy milk
    """
    patterns = [
        r"create (?:a )?text file (?:called|named) (?P<filename>[\w.\- ]+) with (?:this )?context:\s*(?P<content>.+)",
        r"save (?:a )?text file (?:called|named) (?P<filename>[\w.\- ]+) with (?:this )?context:\s*(?P<content>.+)",
        r"write file (?P<filename>[\w.\- ]+):\s*(?P<content>.+)",
    ]

    for pattern in patterns:
        match = re.match(pattern, message, flags=re.IGNORECASE | re.DOTALL)
        if match:
            filename = match.group("filename").strip()
            content = match.group("content").strip()
            path = save_text_file(filename, content)
            return {
                "reply": f"Saved text file to {path}",
                "action": "create_file",
                "path": str(path),
                "filename": path.name,
            }

    return None
