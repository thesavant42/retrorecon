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
import sys
import urllib.parse
from typing import Optional

import requests
import jwt
from flask import Flask, Response
from config import Config
from database import (
    get_db,
    close_connection,
    query_db,
    execute_db,
    init_db,
    ensure_schema,
    create_new_db,
    _sanitize_db_name,
    _sanitize_export_name,
)
from retrorecon.filters import manifest_links, oci_obj
from retrorecon.routes import (
    core_bp,
    notes_bp,
    tools_bp,
    db_bp,
    settings_bp,
    domains_bp,
    docker_bp,
    registry_bp,
    dag_bp,
    oci_bp,
    dagdotdev_bp,
    urls_bp,
)
from retrorecon.services import (
    db_service,
    tags,
    notes,
    jwt_service,
    screenshot_service,
    sitezip_service,
    subdomain_service,
    importer,
    urls as url_service,
)
from retrorecon import progress as progress_mod

app = Flask(__name__)
sys.modules.setdefault('app', sys.modules[__name__])
app.config.from_object(Config)
app.add_template_filter(manifest_links, name="manifest_links")
app.add_template_filter(oci_obj, name="oci_obj")

log_level_name = app.config.get('LOG_LEVEL', 'WARNING').upper()
numeric_level = getattr(logging, log_level_name, logging.WARNING)
logging.basicConfig(level=numeric_level, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

app.jwt = jwt
env_db = app.config.get('DB_ENV')
if env_db:
    if os.path.isabs(env_db):
        app.config['DATABASE'] = env_db
    else:
        app.config['DATABASE'] = os.path.join(app.root_path, 'db', env_db)
else:
    app.config['DATABASE'] = None

app.secret_key = app.config.get('SECRET_KEY', 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY')
app.teardown_appcontext(close_connection)

ITEMS_PER_PAGE = 10
ITEMS_PER_PAGE_OPTIONS = [5, 10, 15, 20, 25]
TEXT_TOOLS_LIMIT = 64 * 1024

THEMES_DIR = os.path.join(app.root_path, 'static', 'themes')
if os.path.isdir(THEMES_DIR):
    AVAILABLE_THEMES = sorted([f for f in os.listdir(THEMES_DIR) if f.endswith('.css')])
else:
    AVAILABLE_THEMES = []

def _parse_theme_colors(filename: str) -> tuple[str, str]:
    bg, fg = '#000000', '#ffffff'
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

IMPORT_PROGRESS_FILE = os.path.join(app.root_path, 'data', 'import_progress.json')
DEMO_DATA_FILE = os.path.join(app.root_path, 'data', 'demo_data.json')
SAVED_TAGS_FILE = os.path.join(app.root_path, 'data', 'saved_tags.json')

app.config['IMPORT_PROGRESS_FILE'] = IMPORT_PROGRESS_FILE
app.config['DEMO_DATA_FILE'] = DEMO_DATA_FILE
app.config['SAVED_TAGS_FILE'] = SAVED_TAGS_FILE

progress_mod.clear_progress(IMPORT_PROGRESS_FILE)

TEMP_DB_NAME = db_service.TEMP_DB_NAME
TEMP_DISPLAY_NAME = db_service.TEMP_DISPLAY_NAME

if not env_db:
    with app.app_context():
        db_service.create_temp_db()

get_db_folder = db_service.get_db_folder
create_temp_db = db_service.create_temp_db
_db_loaded = db_service.db_loaded

set_import_progress = importer.set_import_progress
get_import_progress = importer.get_import_progress
clear_import_progress = importer.clear_import_progress

load_saved_tags = tags.load_saved_tags
save_saved_tags = tags.save_saved_tags

get_notes = notes.get_notes
add_note = notes.add_note
update_note = notes.update_note
delete_note_entry = notes.delete_note_entry
delete_all_notes = notes.delete_all_notes
export_notes_data = notes.export_notes_data

log_jwt_entry = jwt_service.log_entry
delete_jwt_cookies = jwt_service.delete_cookies
update_jwt_cookie = jwt_service.update_cookie
export_jwt_cookie_data = jwt_service.export_cookie_data

export_url_data = url_service.export_url_data

SCREENSHOT_DIR = os.path.join(app.root_path, 'static', 'screenshots')
SITEZIP_DIR = os.path.join(app.root_path, 'static', 'sitezips')
executablePath: Optional[str] = None

save_screenshot_record = screenshot_service.save_record
list_screenshot_data = screenshot_service.list_data
delete_screenshots = screenshot_service.delete_records
def take_screenshot(url: str, user_agent: str = '', spoof_referrer: bool = False) -> bytes:
    return screenshot_service.take_screenshot(url, user_agent, spoof_referrer, executablePath)

save_sitezip_record = sitezip_service.save_record
list_sitezip_data = sitezip_service.list_data
delete_sitezips = sitezip_service.delete_records
def capture_site(url: str, user_agent: str = '', spoof_referrer: bool = False) -> tuple[bytes, bytes]:
    return sitezip_service.capture_site(url, user_agent, spoof_referrer, executablePath)

delete_subdomain = subdomain_service.delete_subdomain

app.register_blueprint(core_bp)
app.register_blueprint(notes_bp)
app.register_blueprint(tools_bp)
app.register_blueprint(db_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(domains_bp)
app.register_blueprint(docker_bp)
app.register_blueprint(registry_bp)
app.register_blueprint(dag_bp)
app.register_blueprint(oci_bp)
app.register_blueprint(dagdotdev_bp)
app.register_blueprint(urls_bp)


@app.after_request
def add_no_cache_headers(response: Response) -> Response:
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response

if __name__ == '__main__':
    if env_db and app.config.get('DATABASE'):
        if not os.path.exists(app.config['DATABASE']):
            create_new_db(os.path.splitext(os.path.basename(env_db))[0])
        else:
            ensure_schema()
    app.run(debug=True)
