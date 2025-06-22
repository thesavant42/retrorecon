from typing import List
from flask import current_app
from retrorecon import saved_tags as saved_tags_mod


def load_saved_tags() -> List[str]:
    """Return the list of saved tags."""
    return saved_tags_mod.load_tags(current_app.config['SAVED_TAGS_FILE'])


def save_saved_tags(tags: List[str]) -> None:
    """Persist ``tags`` to disk."""
    saved_tags_mod.save_tags(current_app.config['SAVED_TAGS_FILE'], tags)
