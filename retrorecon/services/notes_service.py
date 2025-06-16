from typing import Any, Dict, List
import sqlite3
from retrorecon import notes_utils, saved_tags as saved_tags_mod


def load_saved_tags(file_path: str) -> List[str]:
    """Load the list of saved tags from ``file_path``."""
    return saved_tags_mod.load_tags(file_path)


def save_saved_tags(file_path: str, tags: List[str]) -> None:
    """Persist ``tags`` to ``file_path``."""
    saved_tags_mod.save_tags(file_path, tags)


def get_notes(url_id: int) -> List[sqlite3.Row]:
    return notes_utils.get_notes(url_id)


def add_note(url_id: int, content: str) -> int:
    return notes_utils.add_note(url_id, content)


def update_note(note_id: int, content: str) -> None:
    notes_utils.update_note(note_id, content)


def delete_note_entry(note_id: int) -> None:
    notes_utils.delete_note_entry(note_id)


def delete_all_notes(url_id: int) -> None:
    notes_utils.delete_all_notes(url_id)


def export_notes_data() -> List[Dict[str, Any]]:
    return notes_utils.export_notes_data()
