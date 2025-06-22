import os
from typing import Any, Dict, List, Optional, Tuple
from flask import current_app
from retrorecon import sitezip_utils


def sitezip_dir() -> str:
    return os.path.join(current_app.root_path, 'static', 'sitezips')


def save_record(url: str, zip_name: str, screenshot_name: str, thumb_name: str, method: str = 'GET') -> int:
    return sitezip_utils.save_record(sitezip_dir(), url, zip_name, screenshot_name, thumb_name, method)


def list_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return sitezip_utils.list_data(ids)


def delete_records(ids: List[int]) -> None:
    sitezip_utils.delete_records(sitezip_dir(), ids)


def capture_site(url: str, user_agent: str = '', spoof_referrer: bool = False, exec_path: Optional[str] = None) -> Tuple[bytes, bytes]:
    return sitezip_utils.capture_site(url, user_agent, spoof_referrer, exec_path)
