from typing import Any, Dict, List
import sqlite3

from . import notes_utils, text_notes_utils


def get_notes(url_id: int) -> List[sqlite3.Row]:
    """Return all notes for a specific URL."""
    return notes_utils.get_notes(url_id)


def add_note(url_id: int, content: str) -> int:
    """Insert a note and return the row id."""
    return notes_utils.add_note(url_id, content)


def update_note(note_id: int, content: str) -> None:
    """Update an existing note."""
    notes_utils.update_note(note_id, content)


def delete_note_entry(note_id: int) -> None:
    """Delete a note by ID."""
    notes_utils.delete_note_entry(note_id)


def delete_all_notes(url_id: int) -> None:
    """Remove all notes for a URL."""
    notes_utils.delete_all_notes(url_id)


def export_notes_data() -> List[Dict[str, Any]]:
    """Return all notes grouped by URL."""
    return notes_utils.export_notes_data()


def get_text_notes() -> List[sqlite3.Row]:
    """Return all saved text notes."""
    return text_notes_utils.get_text_notes()


def add_text_note(content: str) -> int:
    """Insert a text note and return the row id."""
    return text_notes_utils.add_text_note(content)


def update_text_note(note_id: int, content: str) -> None:
    """Update a text note by ID."""
    text_notes_utils.update_text_note(note_id, content)


def delete_text_note_entry(note_id: int) -> None:
    """Remove a text note by ID."""
    text_notes_utils.delete_text_note(note_id)
