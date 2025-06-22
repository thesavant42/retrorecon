import os
from typing import Any, Dict, List, Optional
from flask import current_app
from retrorecon import screenshot_utils


def screenshot_dir() -> str:
    return os.path.join(current_app.root_path, 'static', 'screenshots')


def save_record(url: str, path: str, thumb: str, method: str = 'GET') -> int:
    return screenshot_utils.save_record(screenshot_dir(), url, path, thumb, method)


def list_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return screenshot_utils.list_data(ids)


def delete_records(ids: List[int]) -> None:
    screenshot_utils.delete_records(screenshot_dir(), ids)


def take_screenshot(url: str, user_agent: str = '', spoof_referrer: bool = False, exec_path: Optional[str] = None) -> bytes:
    return screenshot_utils.take_screenshot(url, user_agent, spoof_referrer, exec_path)
