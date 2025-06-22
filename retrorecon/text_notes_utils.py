from typing import Any, Dict, List
import sqlite3
from typing import List
from markupsafe import escape

from database import query_db, execute_db


def get_text_notes() -> List[sqlite3.Row]:
    """Return all saved text notes."""
    return query_db(
        "SELECT id, content, created_at, updated_at FROM text_notes ORDER BY id"
    )


def add_text_note(content: str) -> int:
    """Insert a text note and return the row id."""
    return execute_db(
        "INSERT INTO text_notes (content) VALUES (?)",
        [escape(content)],
    )


def update_text_note(note_id: int, content: str) -> None:
    """Update a text note by ID."""
    execute_db(
        "UPDATE text_notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [escape(content), note_id],
    )


def delete_text_note(note_id: int) -> None:
    """Remove a text note by ID."""
    execute_db("DELETE FROM text_notes WHERE id = ?", [note_id])
