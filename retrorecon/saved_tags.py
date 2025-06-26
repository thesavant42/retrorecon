import json
import os
import threading
from typing import List, Dict

DEFAULT_COLOR = "#cccccc"

_TAGS_LOCK = threading.Lock()

def load_tags(file_path: str) -> List[Dict[str, str]]:
    """Return saved tag data from ``file_path``.

    The file may contain either a list of strings (legacy format) or a list of
    objects with ``name``, ``color`` and optional ``desc`` fields.
    """
    with _TAGS_LOCK:
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                result = []
                for item in data:
                    if isinstance(item, dict):
                        name = str(item.get("name", "")).strip()
                        color = str(item.get("color", DEFAULT_COLOR)).strip() or DEFAULT_COLOR
                        desc = str(item.get("desc", "")).strip()
                    else:
                        name = str(item).strip()
                        color = DEFAULT_COLOR
                        desc = ""
                    if name:
                        if not name.startswith("#"):
                            name = "#" + name
                        if not color.startswith("#"):
                            color = "#" + color
                        result.append({"name": name, "color": color, "desc": desc})
                return result
        except Exception:
            pass
        return []

def save_tags(file_path: str, tags: List[Dict[str, str]]) -> None:
    """Persist ``tags`` to ``file_path``."""
    with _TAGS_LOCK:
        with open(file_path, 'w') as f:
            json.dump(tags, f, indent=2)
