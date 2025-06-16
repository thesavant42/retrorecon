from typing import Any, Dict, List, Optional
from retrorecon import jwt_utils


def log_jwt_entry(token: str, header: Dict[str, Any], payload: Dict[str, Any], notes: str) -> None:
    jwt_utils.log_entry(token, header, payload, notes)


def delete_jwt_cookies(ids: List[int]) -> None:
    jwt_utils.delete_cookies(ids)


def update_jwt_cookie(jid: int, notes: str) -> None:
    jwt_utils.update_cookie(jid, notes)


def export_jwt_cookie_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return jwt_utils.export_cookie_data(ids)
