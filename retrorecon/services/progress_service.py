from typing import Any, Dict
from retrorecon import progress as progress_mod


def set_import_progress(file_path: str, status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    """Proxy to ``progress.set_progress``."""
    progress_mod.set_progress(file_path, status, message, current, total)


def get_import_progress(file_path: str) -> Dict[str, Any]:
    """Proxy to ``progress.get_progress``."""
    return progress_mod.get_progress(file_path)


def clear_import_progress(file_path: str) -> None:
    """Proxy to ``progress.clear_progress``."""
    progress_mod.clear_progress(file_path)
