import os
from typing import Any, Dict, List, Optional
from flask import current_app
from . import screenshot_utils

# Path to the Chromium executable used by screenshot capture.
# Assign a string path to override Playwright's default.
executable_path: Optional[str] = None


def get_screenshot_dir() -> str:
    """Return the absolute screenshots directory for the running app."""
    return os.path.join(current_app.root_path, 'static', 'screenshots')


def save_screenshot_record(url: str, path: str, thumb: str, method: str = 'GET') -> int:
    """Insert a screenshot record in the database."""
    return screenshot_utils.save_record(get_screenshot_dir(), url, path, thumb, method)


def list_screenshot_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Return screenshot rows as dictionaries."""
    return screenshot_utils.list_data(ids)


def delete_screenshots(ids: List[int]) -> None:
    """Remove screenshot records and files by ID."""
    screenshot_utils.delete_records(get_screenshot_dir(), ids)


def take_screenshot(url: str, user_agent: str = '', spoof_referrer: bool = False) -> bytes:
    """Capture a screenshot of ``url`` and return PNG bytes."""
    return screenshot_utils.take_screenshot(url, user_agent, spoof_referrer, executable_path)
