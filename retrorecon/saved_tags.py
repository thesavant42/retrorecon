import json
import os
import threading
from typing import List

_TAGS_LOCK = threading.Lock()

def load_tags(file_path: str) -> List[str]:
    """Return saved search tags from ``file_path``."""
    with _TAGS_LOCK:
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(t) for t in data]
        except Exception:
            pass
        return []

def save_tags(file_path: str, tags: List[str]) -> None:
    """Persist ``tags`` to ``file_path``."""
    with _TAGS_LOCK:
        with open(file_path, 'w') as f:
            json.dump(tags, f)
