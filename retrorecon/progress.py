import os
import json
import threading
from typing import Any, Dict

_IMPORT_LOCK = threading.Lock()

def set_progress(file_path: str, status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    """Write progress information to ``file_path``."""
    with _IMPORT_LOCK:
        progress = {
            'status': status,
            'message': message,
            'current': current,
            'total': total
        }
        with open(file_path, 'w') as f:
            json.dump(progress, f)

def get_progress(file_path: str) -> Dict[str, Any]:
    """Return the import progress stored at ``file_path``."""
    with _IMPORT_LOCK:
        if not os.path.exists(file_path):
            return {'status': 'idle', 'message': '', 'current': 0, 'total': 0}
        with open(file_path, 'r') as f:
            return json.load(f)

def clear_progress(file_path: str) -> None:
    """Remove ``file_path`` if it exists."""
    with _IMPORT_LOCK:
        if os.path.exists(file_path):
            os.remove(file_path)
