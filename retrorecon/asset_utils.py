import logging
from typing import Any, Dict, List

from database import execute_db, query_db

logger = logging.getLogger(__name__)


def add_asset(path: str, asset_type: str, load_order: int = 0, affinity: str = "") -> int:
    """Insert an asset record and return its row id."""
    return execute_db(
        "INSERT INTO assets (path, asset_type, content_type_affinity, load_order) VALUES (?, ?, ?, ?)",
        [path, asset_type, affinity, load_order],
    )


def list_assets() -> List[Dict[str, Any]]:
    """Return all asset records ordered by ``load_order``."""
    rows = query_db(
        "SELECT path, asset_type, content_type_affinity, load_order FROM assets ORDER BY load_order"
    )
    result: List[Dict[str, Any]] = []
    for r in rows:
        result.append(
            {
                "path": r["path"],
                "asset_type": r["asset_type"],
                "affinity": r["content_type_affinity"],
                "load_order": r["load_order"],
            }
        )
    return result


def delete_asset(path: str) -> None:
    """Remove an asset by path."""
    execute_db("DELETE FROM assets WHERE path = ?", [path])
