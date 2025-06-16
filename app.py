import os
import io
import json
import sqlite3
import zipfile
import threading
import re
import datetime
import base64
import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import jwt
import urllib.parse
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    session,
    jsonify,
    Response,
)
from markupsafe import escape
from config import Config
from database import (
    get_db,
    close_connection,
    query_db,
    execute_db,
    init_db,
    ensure_schema,
    ensure_url_columns,
    create_new_db,
    _sanitize_db_name,
    _sanitize_export_name,
)
from retrorecon import search_utils
from retrorecon.services import (
    set_import_progress as _set_progress,
    get_import_progress as _get_progress,
    clear_import_progress as _clear_progress,
    load_saved_tags,
    save_saved_tags,
    get_notes,
    add_note,
    update_note,
    delete_note_entry,
    delete_all_notes,
    export_notes_data,
    log_jwt_entry,
    delete_jwt_cookies,
    update_jwt_cookie,
    export_jwt_cookie_data,
    save_screenshot_record as _save_screenshot_record,
    list_screenshot_data as _list_screenshot_data,
    delete_screenshots as _delete_screenshots,
    take_screenshot as _take_screenshot,
)

app = Flask(__name__)
app.config.from_object(Config)
logger = logging.getLogger(__name__)
app.jwt = jwt
env_db = app.config.get('DB_ENV')
if env_db:
    app.config['DATABASE'] = env_db if os.path.isabs(env_db) else os.path.join(app.root_path, env_db)
else:
    app.config['DATABASE'] = None
app.secret_key = app.config.get('SECRET_KEY', 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY')
app.teardown_appcontext(close_connection)
ITEMS_PER_PAGE = 10  # default results per page
ITEMS_PER_PAGE_OPTIONS = [5, 10, 15, 20, 25]
TEXT_TOOLS_LIMIT = 64 * 1024  # 64 KB limit for text transformations

THEMES_DIR = os.path.join(app.root_path, 'static', 'themes')
if os.path.isdir(THEMES_DIR):
    AVAILABLE_THEMES = sorted([f for f in os.listdir(THEMES_DIR) if f.endswith('.css')])
else:
    AVAILABLE_THEMES = []

def _parse_theme_colors(filename: str) -> Tuple[str, str]:
    """Return ``(bg, fg)`` colors parsed from the given theme file."""

    bg = '#000000'
    fg = '#ffffff'
    try:
        with open(os.path.join(THEMES_DIR, filename)) as fh:
            for line in fh:
                if '--bg-color' in line:
                    bg = line.split(':')[1].strip().rstrip(';')
                elif '--fg-color' in line:
                    fg = line.split(':')[1].strip().rstrip(';')
                if 'font-family' in line:
                    break
    except OSError:
        pass
    return bg, fg

THEME_SWATCHES = {t: _parse_theme_colors(t) for t in AVAILABLE_THEMES}

BACKGROUNDS_DIR = os.path.join(app.root_path, 'static', 'img')
if os.path.isdir(BACKGROUNDS_DIR):
    AVAILABLE_BACKGROUNDS = sorted([
        f for f in os.listdir(BACKGROUNDS_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
else:
    AVAILABLE_BACKGROUNDS = []

IMPORT_PROGRESS_FILE = os.path.join(app.root_path, 'import_progress.json')
DEMO_DATA_FILE = os.path.join(app.root_path, 'data/demo_data.json')
SAVED_TAGS_FILE = os.path.join(app.root_path, 'saved_tags.json')

def _db_loaded() -> bool:
    """Return True if a database file is currently configured and exists."""

    return bool(app.config.get('DATABASE') and os.path.exists(app.config['DATABASE']))

SCREENSHOT_DIR = os.path.join(app.root_path, 'static', 'screenshots')
executablePath: Optional[str] = None


def set_import_progress(status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    _set_progress(IMPORT_PROGRESS_FILE, status, message, current, total)


def get_import_progress() -> Dict[str, Any]:
    return _get_progress(IMPORT_PROGRESS_FILE)


def clear_import_progress() -> None:
    _clear_progress(IMPORT_PROGRESS_FILE)


def take_screenshot(url: str, user_agent: str = '', spoof_referrer: bool = False) -> bytes:
    return _take_screenshot(url, user_agent, spoof_referrer, executablePath)


def save_screenshot_record(url: str, path: str, thumb: str, method: str = 'GET') -> int:
    return _save_screenshot_record(SCREENSHOT_DIR, url, path, thumb, method)


def list_screenshot_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return _list_screenshot_data(ids)


def delete_screenshots(ids: List[int]) -> None:
    _delete_screenshots(SCREENSHOT_DIR, ids)



from retrorecon.routes import (
    notes_bp,
    tools_bp,
    db_bp,
    settings_bp,
    urls_bp,
    api_client_bp,
)
from retrorecon.routes.urls import index
app.register_blueprint(notes_bp)
app.register_blueprint(tools_bp)
app.register_blueprint(db_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(urls_bp)
app.register_blueprint(api_client_bp)

if __name__ == '__main__':
    if env_db and app.config.get('DATABASE'):
        if not os.path.exists(app.config['DATABASE']):
            create_new_db(os.path.splitext(os.path.basename(env_db))[0])
        else:
            ensure_schema()
    app.run(debug=True)
