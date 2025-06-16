from typing import Any, Dict, List, Optional
from retrorecon import screenshot_utils


def save_screenshot_record(dir_path: str, url: str, path: str, thumb: str, method: str = 'GET') -> int:
    return screenshot_utils.save_record(dir_path, url, path, thumb, method)


def list_screenshot_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return screenshot_utils.list_data(ids)


def delete_screenshots(dir_path: str, ids: List[int]) -> None:
    screenshot_utils.delete_records(dir_path, ids)


def take_screenshot(url: str, user_agent: str = '', spoof_referrer: bool = False, executable_path: Optional[str] = None) -> bytes:
    return screenshot_utils.take_screenshot(url, user_agent, spoof_referrer, executable_path)
