import jwt as pyjwt
from typing import Any, Dict, List, Optional

from . import jwt_utils

# expose the PyJWT module for encoding/decoding
jwt = pyjwt


def log_jwt_entry(token: str, header: Dict[str, Any], payload: Dict[str, Any], notes: str) -> None:
    """Log a decoded JWT entry via ``jwt_utils``."""
    jwt_utils.log_entry(token, header, payload, notes)


def delete_jwt_cookies(ids: List[int]) -> None:
    """Delete JWT cookie records by ID."""
    jwt_utils.delete_cookies(ids)


def update_jwt_cookie(jid: int, notes: str) -> None:
    """Update the notes for a JWT cookie entry."""
    jwt_utils.update_cookie(jid, notes)


def export_jwt_cookie_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Return JWT cookie entries for optional IDs."""
    return jwt_utils.export_cookie_data(ids)
