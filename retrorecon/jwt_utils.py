import json
from typing import Any, Dict, List, Optional

from database import execute_db, query_db


def log_entry(token: str, header: Dict[str, Any], payload: Dict[str, Any], notes: str) -> None:
    """Insert a decoded JWT into the ``jwt_cookies`` table."""
    execute_db(
        "INSERT INTO jwt_cookies (token, header, payload, notes) VALUES (?, ?, ?, ?)",
        [token, json.dumps(header), json.dumps(payload), notes],
    )


def delete_cookies(ids: List[int]) -> None:
    """Delete JWT cookie log entries by ID."""
    if not ids:
        return
    for jid in ids:
        execute_db("DELETE FROM jwt_cookies WHERE id = ?", [jid])


def update_cookie(jid: int, notes: str) -> None:
    """Update the notes for a JWT cookie entry."""
    execute_db("UPDATE jwt_cookies SET notes = ? WHERE id = ?", [notes, jid])


def export_cookie_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Return JWT cookie entries as dictionaries."""
    where = ""
    params: List[Any] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        where = f"WHERE id IN ({placeholders})"
        params.extend(ids)
    rows = query_db(
        f"SELECT id, token, header, payload, notes, created_at FROM jwt_cookies {where} ORDER BY id DESC",
        params,
    )
    result = []
    for r in rows:
        try:
            hdr = json.loads(r["header"])
        except Exception:
            hdr = {}
        try:
            pl = json.loads(r["payload"])
        except Exception:
            pl = {}
        result.append(
            {
                "id": r["id"],
                "token": r["token"],
                "issuer": pl.get("iss", ""),
                "alg": hdr.get("alg", ""),
                "claims": list(pl.keys()),
                "notes": r["notes"],
                "created_at": r["created_at"],
            }
        )
    return result
