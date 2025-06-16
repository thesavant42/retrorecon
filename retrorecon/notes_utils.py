from typing import Any, Dict, List
import sqlite3
from markupsafe import escape

from database import query_db, execute_db


def get_notes(url_id: int) -> List[sqlite3.Row]:
    """Return all notes for a specific URL."""
    return query_db(
        "SELECT id, url_id, content, created_at, updated_at FROM notes WHERE url_id = ? ORDER BY id",
        [url_id],
    )


def add_note(url_id: int, content: str) -> int:
    """Insert a note and return the row id."""
    return execute_db(
        "INSERT INTO notes (url_id, content) VALUES (?, ?)",
        [url_id, escape(content)],
    )


def update_note(note_id: int, content: str) -> None:
    """Update an existing note."""
    execute_db(
        "UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [escape(content), note_id],
    )


def delete_note_entry(note_id: int) -> None:
    """Delete a note by ID."""
    execute_db("DELETE FROM notes WHERE id = ?", [note_id])


def delete_all_notes(url_id: int) -> None:
    """Remove all notes for a URL."""
    execute_db("DELETE FROM notes WHERE url_id = ?", [url_id])


def export_notes_data() -> List[Dict[str, Any]]:
    """Return all notes grouped by URL."""
    rows = query_db(
        "SELECT urls.url, notes.content FROM notes JOIN urls ON notes.url_id = urls.id ORDER BY urls.url, notes.id"
    )
    grouped: Dict[str, List[str]] = {}
    for r in rows:
        grouped.setdefault(r["url"], []).append(r["content"])
    return [{"url": u, "notes": n} for u, n in grouped.items()]
