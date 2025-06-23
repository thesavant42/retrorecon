import os
import io
import zipfile
import threading
import re
import datetime
import base64
import logging
import sys
from typing import Any, Dict, List, Optional, Tuple, Union

from retrorecon import theme

import requests
from retrorecon import jwt_service
import urllib.parse
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    send_from_directory,
    session,
    jsonify,
    Response,
)

# defer importing the OCI blueprint to avoid circular imports
oci = None
from markupsafe import escape
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
from retrorecon import (
    saved_tags as saved_tags_mod,
    search_utils,
    import_utils,
    status as status_mod,
    app_utils,
    middleware,
)
from retrorecon.filters import manifest_links, oci_obj

app = Flask(__name__)
sys.modules.setdefault('app', sys.modules[__name__])
app.config.from_object(Config)
app.add_template_filter(manifest_links, name="manifest_links")
app.add_template_filter(oci_obj, name="oci_obj")



def get_db_folder() -> str:
    """Return the folder where database files are stored."""
    return app_utils.get_db_folder(app.root_path)

log_level_name = app.config.get('LOG_LEVEL', 'WARNING').upper()
numeric_level = getattr(logging, log_level_name, logging.WARNING)
logging.basicConfig(level=numeric_level, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)
env_db = app.config.get('DB_ENV')
if env_db:
    app.config['DATABASE'] = env_db if os.path.isabs(env_db) else os.path.join(app_utils.get_db_folder(app.root_path), env_db)
else:
    app.config['DATABASE'] = None
app.secret_key = app.config.get('SECRET_KEY', 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY')
app.teardown_appcontext(close_connection)
ITEMS_PER_PAGE = 10  # default results per page
ITEMS_PER_PAGE_OPTIONS = [5, 10, 15, 20, 25]
TEXT_TOOLS_LIMIT = 64 * 1024  # 64 KB limit for text transformations

(
    THEMES_DIR,
    AVAILABLE_THEMES,
    THEME_SWATCHES,
    BACKGROUNDS_DIR,
    AVAILABLE_BACKGROUNDS,
) = theme.load_theme_data(app.root_path)

IMPORT_PROGRESS_FILE = os.path.join(app.root_path, 'data', 'import_progress.json')
DEMO_DATA_FILE = os.path.join(app.root_path, 'data', 'demo_data.json')
SAVED_TAGS_FILE = os.path.join(app.root_path, 'data', 'saved_tags.json')

# Clear any stale import progress from previous runs
import_utils.clear_import_progress(IMPORT_PROGRESS_FILE)

# Temporary database handling
TEMP_DB_NAME = app_utils.TEMP_DB_NAME
TEMP_DISPLAY_NAME = app_utils.TEMP_DISPLAY_NAME



if not env_db:
    with app.app_context():
        app_utils._create_temp_db()






from retrorecon.routes import (
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
    swagger_bp,
    overview_bp,
    tags_bp,
    assets_bp,
    import_bp,
    status_bp,
)
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
app.register_blueprint(swagger_bp)
app.register_blueprint(overview_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(import_bp)
app.register_blueprint(status_bp)
app.after_request(middleware.add_no_cache_headers)



if __name__ == '__main__':
    if env_db and app.config.get('DATABASE'):
        if not os.path.exists(app.config['DATABASE']):
            create_new_db(os.path.splitext(os.path.basename(env_db))[0])
        else:
            ensure_schema()
    app.run(debug=True)
