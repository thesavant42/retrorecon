from typing import Any, Dict, List
from retrorecon import notes_utils


def get_notes(url_id: int) -> List:
    """Return notes for a URL."""
    return notes_utils.get_notes(url_id)


def add_note(url_id: int, content: str) -> int:
    """Insert a note and return its ID."""
    return notes_utils.add_note(url_id, content)


def update_note(note_id: int, content: str) -> None:
    """Update an existing note."""
    notes_utils.update_note(note_id, content)


def delete_note_entry(note_id: int) -> None:
    """Delete a note by ID."""
    notes_utils.delete_note_entry(note_id)


def delete_all_notes(url_id: int) -> None:
    """Delete all notes for ``url_id``."""
    notes_utils.delete_all_notes(url_id)


def export_notes_data() -> List[Dict[str, Any]]:
    """Return all notes grouped by URL."""
    return notes_utils.export_notes_data()
