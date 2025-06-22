from typing import List
import sys
from flask import current_app
from retrorecon import saved_tags as saved_tags_mod


def _tags_file() -> str:
    app_mod = sys.modules.get('app')
    if app_mod and getattr(app_mod, 'SAVED_TAGS_FILE', None):
        return app_mod.SAVED_TAGS_FILE
    try:
        if current_app and 'SAVED_TAGS_FILE' in current_app.config:
            return current_app.config['SAVED_TAGS_FILE']
    except Exception:
        pass
    return 'data/saved_tags.json'


def load_saved_tags() -> List[str]:
    """Return the list of saved tags."""
    return saved_tags_mod.load_tags(_tags_file())


def save_saved_tags(tags: List[str]) -> None:
    """Persist ``tags`` to disk."""
    saved_tags_mod.save_tags(_tags_file(), tags)
