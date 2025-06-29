import json
import os
import threading
from typing import List

_TAGS_LOCK = threading.Lock()

def load_tags(file_path: str) -> List[str]:
    """Return saved search tags from ``file_path``.

    Handles legacy data which stored dictionaries with a ``name`` field.
    """
    with _TAGS_LOCK:
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except Exception:
            return []

        result: List[str] = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    name = str(item.get("name", "")).strip()
                else:
                    name = str(item).strip()
                if not name:
                    continue
                if not name.startswith("#"):
                    name = "#" + name.lstrip("#")
                if name not in result:
                    result.append(name)
        return result

def save_tags(file_path: str, tags: List[str]) -> None:
    """Persist ``tags`` to ``file_path``."""
    with _TAGS_LOCK:
        clean: List[str] = []
        for tag in tags:
            name = str(tag).strip()
            if not name:
                continue
            if not name.startswith("#"):
                name = "#" + name.lstrip("#")
            if name not in clean:
                clean.append(name)
        with open(file_path, "w") as f:
            json.dump(clean, f)
