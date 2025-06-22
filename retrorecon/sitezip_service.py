import os
from typing import Any, Dict, List, Optional, Tuple
from flask import current_app
from . import sitezip_utils, screenshot_service

# Path to the Chromium executable forwarded to site capture.
executable_path: Optional[str] = None


def get_sitezip_dir() -> str:
    """Return the absolute sitezips directory for the running app."""
    return os.path.join(current_app.root_path, 'static', 'sitezips')


def save_sitezip_record(url: str, zip_name: str, screenshot_name: str, thumb_name: str, method: str = 'GET') -> int:
    """Insert a sitezip record and ensure the directory exists."""
    return sitezip_utils.save_record(get_sitezip_dir(), url, zip_name, screenshot_name, thumb_name, method)


def list_sitezip_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Return sitezip rows as dictionaries."""
    return sitezip_utils.list_data(ids)


def delete_sitezips(ids: List[int]) -> None:
    """Delete sitezip records and associated files."""
    sitezip_utils.delete_records(get_sitezip_dir(), ids)


def capture_site(url: str, user_agent: str = '', spoof_referrer: bool = False) -> Tuple[bytes, bytes]:
    """Capture the page HTML and screenshot as a ZIP and PNG."""
    path = executable_path if executable_path is not None else screenshot_service.executable_path
    return sitezip_utils.capture_site(url, user_agent, spoof_referrer, path)
