import os
from flask import current_app
from database import init_db

TEMP_DB_NAME = 'temp.db'
TEMP_DISPLAY_NAME = 'UNSAVED'


def get_db_folder() -> str:
    """Return the folder used for database files."""
    folder = os.path.join(current_app.root_path, 'db')
    os.makedirs(folder, exist_ok=True)
    return folder


def create_temp_db() -> None:
    """Create a fresh temporary database."""
    db_path = os.path.join(get_db_folder(), TEMP_DB_NAME)
    current_app.config['DATABASE'] = db_path
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db()


def db_loaded() -> bool:
    """Return ``True`` if the configured database exists."""
    path = current_app.config.get('DATABASE')
    return bool(path and os.path.exists(path))
