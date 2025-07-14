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
    progress as progress_mod,
    saved_tags as saved_tags_mod,
    notes_utils,
    text_notes_utils,
    jwt_utils,
    search_utils,
    screenshot_utils,
    httpolaroid_utils,
    subdomain_utils,
    status as status_mod,
)
from retrorecon.filters import manifest_links, oci_obj, manifest_table, wb_timestamp
from mcp_manager import start_mcp_sqlite

app = Flask(__name__)
sys.modules.setdefault('app', sys.modules[__name__])
app.start_mcp_sqlite = start_mcp_sqlite
app.config.from_object(Config)
app.add_template_filter(manifest_links, name="manifest_links")
app.add_template_filter(oci_obj, name="oci_obj")
app.add_template_filter(manifest_table, name="manifest_table")
app.add_template_filter(wb_timestamp, name="wb_timestamp")


@app.route('/favicon.ico', endpoint='core.favicon_ico')
def favicon_ico() -> Response:
    """Serve the favicon.ico from the application root."""
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/favicon.svg')
def favicon_svg() -> Response:
    """Serve the favicon.svg from the application root."""
    return send_from_directory(app.root_path, 'favicon.svg', mimetype='image/svg+xml')

def get_db_folder() -> str:
    """Return the folder where database files are stored."""
    folder = os.path.join(app.root_path, 'db')
    os.makedirs(folder, exist_ok=True)
    return folder
log_level_name = app.config.get('LOG_LEVEL', 'WARNING').upper()
numeric_level = getattr(logging, log_level_name, logging.WARNING)
logging.basicConfig(level=numeric_level, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)
app.jwt = jwt
env_db = app.config.get('DB_ENV')
if env_db:
    app.config['DATABASE'] = env_db if os.path.isabs(env_db) else os.path.join(get_db_folder(), env_db)
else:
    app.config['DATABASE'] = None
app.secret_key = app.config.get('SECRET_KEY', 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY')
app.teardown_appcontext(close_connection)
ITEMS_PER_PAGE = 10  # default results per page
ITEMS_PER_PAGE_OPTIONS = [5, 10, 15, 20, 25]
TEXT_TOOLS_LIMIT = 64 * 1024  # 64 KB limit for text transformations
APP_VERSION = '1.5.0'

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

IMPORT_PROGRESS_FILE = os.path.join(app.root_path, 'data', 'import_progress.json')
DEMO_DATA_FILE = os.path.join(app.root_path, 'data', 'demo_data.json')
SAVED_TAGS_FILE = os.path.join(app.root_path, 'data', 'saved_tags.json')

# Clear any stale import progress from previous runs
progress_mod.clear_progress(IMPORT_PROGRESS_FILE)

# Temporary database handling
TEMP_DB_NAME = 'temp.db'
TEMP_DISPLAY_NAME = 'UNSAVED'


def _create_temp_db() -> None:
    """Create a fresh temporary database for this session."""
    app.config['DATABASE'] = os.path.join(get_db_folder(), TEMP_DB_NAME)
    if os.path.exists(app.config['DATABASE']):
        os.remove(app.config['DATABASE'])
    init_db()
    app.mcp_server = start_mcp_sqlite(app.config['DATABASE'])


if not env_db:
    with app.app_context():
        _create_temp_db()

def _db_loaded() -> bool:
    """Return True if a database file is currently configured and exists."""

    return bool(app.config.get('DATABASE') and os.path.exists(app.config['DATABASE']))

def set_import_progress(status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    progress_mod.set_progress(IMPORT_PROGRESS_FILE, status, message, current, total)


def get_import_progress() -> Dict[str, Any]:
    return progress_mod.get_progress(IMPORT_PROGRESS_FILE)


def clear_import_progress() -> None:
    progress_mod.clear_progress(IMPORT_PROGRESS_FILE)


def load_saved_tags() -> List[str]:
    return saved_tags_mod.load_tags(SAVED_TAGS_FILE)


def save_saved_tags(tags: List[str]) -> None:
    saved_tags_mod.save_tags(SAVED_TAGS_FILE, tags)


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


def get_text_notes() -> List[sqlite3.Row]:
    return text_notes_utils.get_text_notes()


def add_text_note(content: str) -> int:
    return text_notes_utils.add_text_note(content)


def update_text_note(note_id: int, content: str) -> None:
    text_notes_utils.update_text_note(note_id, content)


def delete_text_note_entry(note_id: int) -> None:
    text_notes_utils.delete_text_note(note_id)


def log_jwt_entry(token: str, header: Dict[str, Any], payload: Dict[str, Any], notes: str) -> None:
    jwt_utils.log_entry(token, header, payload, notes)


def delete_jwt_cookies(ids: List[int]) -> None:
    jwt_utils.delete_cookies(ids)


def update_jwt_cookie(jid: int, notes: str) -> None:
    jwt_utils.update_cookie(jid, notes)


def export_jwt_cookie_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return jwt_utils.export_cookie_data(ids)


def export_url_data(ids: Optional[List[int]] = None, query: str = '') -> List[Dict[str, Any]]:
    """Return URL records filtered by ids or search query."""
    where = []
    params: List[Any] = []
    if ids:
        placeholders = ','.join('?' for _ in ids)
        where.append(f'id IN ({placeholders})')
        params.extend(ids)
    if query:
        try:
            search_sql, search_params = search_utils.build_search_sql(query)
            where.append(search_sql)
            params.extend(search_params)
        except Exception:
            where.append(
                '('
                'url LIKE ? OR tags LIKE ? OR '
                'CAST(timestamp AS TEXT) LIKE ? OR '
                'CAST(status_code AS TEXT) LIKE ? OR '
                'mime_type LIKE ?'
                ')'
            )
            params.extend([f'%{query}%'] * 5)
    where_sql = 'WHERE ' + ' AND '.join(where) if where else ''
    rows = query_db(
        f"SELECT id, url, timestamp, status_code, mime_type, tags FROM urls {where_sql} ORDER BY id",
        params,
    )
    result = []
    for r in rows:
        result.append(
            {
                'id': r['id'],
                'url': r['url'],
                'timestamp': r['timestamp'],
                'status_code': r['status_code'],
                'mime_type': r['mime_type'],
                'tags': r['tags'],
            }
        )
    return result


SCREENSHOT_DIR = os.path.join(app.root_path, 'static', 'screenshots')
SITEZIP_DIR = os.path.join(app.root_path, 'static', 'sitezips')
executablePath: Optional[str] = None


def save_screenshot_record(
    url: str,
    path: str,
    thumb: str,
    method: str = 'GET',
    status_code: int = 0,
    ip_addresses: str = '',
) -> int:
    return screenshot_utils.save_record(
        SCREENSHOT_DIR,
        url,
        path,
        thumb,
        method,
        status_code,
        ip_addresses,
    )


def list_screenshot_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return screenshot_utils.list_data(ids)


def delete_screenshots(ids: List[int]) -> None:
    screenshot_utils.delete_records(SCREENSHOT_DIR, ids)


def take_screenshot(
    url: str,
    user_agent: str = '',
    spoof_referrer: bool = False,
    log_path: Optional[str] = None,
) -> Tuple[bytes, int, str]:
    return screenshot_utils.take_screenshot(
        url, user_agent, spoof_referrer, executablePath, log_path
    )


def save_httpolaroid_record(
    url: str,
    zip_name: str,
    screenshot_name: str,
    thumb_name: str,
    method: str = 'GET',
    status_code: int = 0,
    ip_addresses: str = '',
) -> int:
    return httpolaroid_utils.save_record(
        SITEZIP_DIR,
        url,
        zip_name,
        screenshot_name,
        thumb_name,
        method,
        status_code,
        ip_addresses,
    )


def list_httpolaroid_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    return httpolaroid_utils.list_data(ids)


def delete_httpolaroids(ids: List[int]) -> None:
    httpolaroid_utils.delete_records(SITEZIP_DIR, ids)


def capture_snap(
    url: str,
    user_agent: str = '',
    spoof_referrer: bool = False,
    log_path: Optional[str] = None,
    har_path: Optional[str] = None,
) -> Tuple[bytes, bytes, int, str]:
    return httpolaroid_utils.capture_site(
        url, user_agent, spoof_referrer, executablePath, log_path, har_path
    )


def delete_subdomain(root_domain: str, subdomain: str) -> None:
    """Remove a subdomain entry from the database."""
    subdomain_utils.delete_record(root_domain, subdomain)


def update_subdomain(
    old_root_domain: str, old_subdomain: str, new_root_domain: str, new_subdomain: str
) -> None:
    """Rename a subdomain entry in the database."""
    subdomain_utils.update_record(
        old_root_domain, old_subdomain, new_root_domain, new_subdomain
    )


@app.route('/', methods=['GET'])
def index() -> str:
    """Render the main search page or serve registry explorer views."""
    repo_param = request.args.get("repo")
    image_param = request.args.get("image")
    if repo_param:
        from retrorecon.routes.oci import repo_view
        return repo_view(repo_param)
    if image_param:
        from retrorecon.routes.oci import image_view
        return image_view(image_param)

    q_param = request.args.get('q')
    if q_param is None:
        q = session.get('search_query', '').strip()
    else:
        q = q_param.strip()
        session['search_query'] = q
    select_all_matching = request.args.get('select_all_matching', 'false').lower() == 'true'
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    tool = request.args.get('tool')
    if request.path == '/tools/jwt':
        tool = 'jwt'
    elif request.path == '/tools/screenshotter':
        tool = 'screenshot'
    elif request.path == '/tools/text_tools':
        tool = 'text'
    elif request.path == '/tools/markdown':
        tool = 'markdown'
    elif request.path == '/tools/readme':
        tool = 'readme'
    elif request.path == '/tools/about':
        tool = 'about'
    elif request.path == '/tools/demo':
        tool = 'demo'

    sort = request.args.get('sort', 'id')
    direction = request.args.get('dir', 'desc').lower()
    if direction not in ['asc', 'desc']:
        direction = 'desc'

    try:
        items_per_page = int(session.get('items_per_page', ITEMS_PER_PAGE))
    except ValueError:
        items_per_page = ITEMS_PER_PAGE
    if items_per_page not in ITEMS_PER_PAGE_OPTIONS:
        items_per_page = ITEMS_PER_PAGE

    if _db_loaded():
        where_clauses = []
        params = []
        if q:
            try:
                search_sql, search_params = search_utils.build_search_sql(q)
                where_clauses.append(search_sql)
                params.extend(search_params)
            except Exception:
                where_clauses.append(
                    "("
                    "url LIKE ? OR tags LIKE ? OR "
                    "CAST(timestamp AS TEXT) LIKE ? OR "
                    "CAST(status_code AS TEXT) LIKE ? OR "
                    "mime_type LIKE ?"
                    ")"
                )
                params.extend([f"%{q}%"] * 5)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sort_map = {
            'url': 'url',
            'timestamp': 'timestamp',
            'status_code': 'status_code',
            'mime_type': 'mime_type',
            'id': 'id'
        }
        sort_col = sort_map.get(sort, 'id')

        count_sql = f"SELECT COUNT(*) AS cnt FROM urls {where_sql}"
        count_row = query_db(count_sql, params, one=True)
        total_count = count_row['cnt'] if count_row else 0

        total_pages = max(1, (total_count + items_per_page - 1) // items_per_page)

        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        offset = (page - 1) * items_per_page
        select_sql = f"""
            SELECT id, url, timestamp, status_code, mime_type, tags
            FROM urls
            {where_sql}
            ORDER BY {sort_col} {direction.upper()}
            LIMIT ? OFFSET ?
        """
        rows = query_db(select_sql, params + [items_per_page, offset])
    else:
        rows = []
        total_pages = 1
        total_count = 0

    if _db_loaded():
        actual_name = os.path.basename(app.config['DATABASE'])
        if actual_name == TEMP_DB_NAME:
            actual_name = TEMP_DISPLAY_NAME
    else:
        actual_name = '(none)'
    if session.get('db_display_name') != actual_name:
        session['db_display_name'] = actual_name
    db_name = session['db_display_name']

    if not _db_loaded() and db_name not in ('(none)', TEMP_DISPLAY_NAME):
        missing_path = os.path.join(get_db_folder(), db_name)
        if not os.path.exists(missing_path) and not session.get('missing_db_warned'):
            flash(
                f"\N{WARNING SIGN} Previously loaded database '{db_name}' not found. Please select another or import a fresh copy.",
                'error'
            )
            session['missing_db_warned'] = True
    elif _db_loaded():
        session.pop('missing_db_warned', None)

    try:
        saved_dbs = sorted([
            f for f in os.listdir(get_db_folder())
            if f.endswith('.db') and os.path.isfile(os.path.join(get_db_folder(), f))
        ])
    except OSError:
        saved_dbs = []

    default_theme = 'nostalgia.css' if 'nostalgia.css' in AVAILABLE_THEMES else (AVAILABLE_THEMES[0] if AVAILABLE_THEMES else '')
    current_theme = session.get('theme', default_theme)

    default_background = AVAILABLE_BACKGROUNDS[0] if AVAILABLE_BACKGROUNDS else ''
    current_background = session.get('background', default_background)

    panel_opacity = float(session.get('panel_opacity', 0.75))

    search_history = session.get('search_history', [])
    if q:
        if q in search_history:
            search_history.remove(q)
        search_history.insert(0, q)
        session['search_history'] = search_history[:10]

    from retrorecon.routes.dynamic import dynamic_template

    return dynamic_template(
        'index.html',
        urls=rows,
        page=page,
        total_pages=total_pages,
        q=q,
        themes=AVAILABLE_THEMES,
        theme_swatches=THEME_SWATCHES,
        current_theme=current_theme,
        backgrounds=AVAILABLE_BACKGROUNDS,
        current_background=current_background,
        panel_opacity=panel_opacity,
        total_count=total_count,
        items_per_page=items_per_page,
        db_name=db_name,
        saved_dbs=saved_dbs,
        search_history=search_history,
        current_sort=sort,
        current_dir=direction,
        open_tool=tool,
        select_all_matching=select_all_matching,
        app_version=APP_VERSION
    )


@app.route('/fetch_cdx', methods=['POST'])
def fetch_cdx() -> Response:
    """Fetch CDX data for a domain and insert new URLs with pagination."""
    domain = request.form.get('domain', '').strip().lower()
    resume_key = request.form.get('resume_key', '').strip()
    if not domain:
        flash("No domain provided for CDX fetch.", "error")
        return redirect(url_for('index'))
    if not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
        flash("Invalid domain value.", "error")
        return redirect(url_for('index'))
    if not _db_loaded():
        flash("No database loaded.", "error")
        return redirect(url_for('index'))

    base_api = (
        'https://web.archive.org/cdx/search/cdx'
        '?url=*.{domain}/*&output=json&fl=original,timestamp,statuscode,mimetype'
        '&collapse=urlkey&limit=1000&showResumeKey=true'
    ).format(domain=domain)

    inserted = 0
    page = 0
    while True:
        url = base_api
        if resume_key:
            url += f"&resumeKey={resume_key}"

        status_mod.push_status('cdx_api_waiting', domain)
        try:
            status_mod.push_status('cdx_api_downloading', url)
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            status_mod.push_status('cdx_api_download_complete', url)
        except Exception as e:
            flash(f"Error fetching CDX data: {e}", "error")
            return redirect(url_for('index'))

        next_key = None
        if data and isinstance(data[-1], list) and len(data[-1]) == 1:
            next_key = str(data[-1][0])
            data = data[:-1]
        elif data and isinstance(data[-1], dict) and 'resumeKey' in data[-1]:
            next_key = str(data[-1].get('resumeKey'))
            data = data[:-1]

        for idx, row in enumerate(data):
            if idx == 0 or not row:
                continue
            original_url = row[0]
            timestamp = row[1] if len(row) > 1 else None
            if len(row) > 2:
                status_raw = str(row[2])
                status_code = int(status_raw) if status_raw.isdigit() else None
            else:
                status_code = None
            mime_type = row[3] if len(row) > 3 else None
            existing = query_db(
                "SELECT id FROM urls WHERE url = ?",
                [original_url],
                one=True
            )
            if existing:
                continue
            entry_domain = urllib.parse.urlsplit(original_url).hostname or domain
            execute_db(
                "INSERT INTO urls (url, domain, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?, ?)",
                [original_url, entry_domain, timestamp, status_code, mime_type, ""]
            )
            inserted += 1

        page += 1
        status_mod.push_status('cdx_page_processed', str(page))

        if not next_key:
            break
        resume_key = next_key
        status_mod.push_status('cdx_resume_key', resume_key)

    message = f"Fetched CDX for {domain}: inserted {inserted} new URLs."
    status_mod.push_status('cdx_import_complete', str(inserted))
    try:
        subdomain_utils.scrape_from_urls(domain)
    except Exception:
        pass
    if request.form.get('ajax') == '1' or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({"inserted": inserted, "message": message})
    flash(message, "success")
    return redirect(url_for('index'))

def _background_import(file_content: bytes) -> None:
    """Background thread handler for JSON/line-delimited imports."""
    try:
        content = file_content.decode('utf-8').strip()
        records = []

        # Try JSON array first
        try:
            data = json.loads(content)
            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                records = [{"url": url, "tags": ""} for url in data]
            elif isinstance(data, list) and all(isinstance(item, dict) for item in data):
                records = [
                    {
                        "url": rec.get('url', '').strip(),
                        "timestamp": rec.get('timestamp'),
                        "status_code": rec.get('status_code'),
                        "mime_type": rec.get('mime_type'),
                        "tags": rec.get('tags', '').strip()
                    }
                    for rec in data if rec.get('url', '').strip()
                ]
        except Exception:
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    url = rec.get('url', '').strip()
                    if url:
                        records.append({
                            "url": url,
                            "timestamp": rec.get('timestamp'),
                            "status_code": rec.get('status_code'),
                            "mime_type": rec.get('mime_type'),
                            "tags": rec.get('tags', '').strip()
                        })
                except Exception:
                    continue

        total = len(records)
        set_import_progress('in_progress', '', 0, total)
        db = sqlite3.connect(app.config['DATABASE'])
        c = db.cursor()
        inserted = 0
        for idx, rec in enumerate(records):
            try:
                c.execute(
                    "INSERT OR IGNORE INTO urls (url, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?)",
                    (
                        rec['url'],
                        rec.get('timestamp'),
                        rec.get('status_code'),
                        rec.get('mime_type'),
                        rec['tags']
                    )
                )
            except Exception:
                continue
            inserted += 1
            # Update progress every 10 or on last
            if idx % 10 == 0 or idx + 1 == total:
                set_import_progress('in_progress', '', idx + 1, total)
        db.commit()
        db.close()
        set_import_progress('done', f"Imported {inserted} of {total} records.", inserted, total)
    except Exception as e:
        set_import_progress('failed', str(e), 0, 0)

@app.route('/import_file', methods=['POST'])
@app.route('/import_json', methods=['POST'])
def import_file() -> Response:
    """Import a JSON list of records into the current database."""
    file = (
        request.files.get('import_file')
        or request.files.get('json_file')
    )
    if not file:
        flash("No file uploaded for import.", "error")
        return redirect(url_for('index'))

    filename = file.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext != 'json':
        flash('Please upload a JSON file.', 'error')
        return redirect(url_for('index'))

    if not _db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))

    clear_import_progress()
    file_content = file.read()
    set_import_progress('starting', 'Starting import...', 0, 0)
    thread = threading.Thread(target=_background_import, args=(file_content,))
    thread.start()
    flash('Import started! Progress will be shown below.', 'success')
    return redirect(url_for('index'))

@app.route('/import_progress', methods=['GET'])
def import_progress() -> Response:
    """Return JSON describing the current import progress."""
    prog = get_import_progress()
    if request.args.get('clear') == '1' and prog.get('status') in ('done', 'failed'):
        clear_import_progress()
    # Always supply progress and total, and message for UI
    return jsonify({
        'status': prog.get('status', 'idle'),
        'progress': prog.get('current', 0),
        'total': prog.get('total', 0),
        'detail': prog.get('message', '')
    })


@app.route('/status', methods=['GET'])
def status_route() -> Response:
    """Return the most recent status event and clear the queue."""
    evt = status_mod.pop_status()
    last = evt
    while True:
        nxt = status_mod.pop_status()
        if not nxt:
            break
        last = nxt
    if not last:
        return ('', 204)
    return jsonify({'code': last[0], 'message': last[1]})

@app.route('/add_tag', methods=['POST'])
def add_tag() -> Response:
    """Append a tag to the selected URL entry."""
    if not _db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    entry_id = request.form.get('entry_id')
    new_tag = request.form.get('new_tag', '').strip()
    if not entry_id or not new_tag:
        flash("Missing URL ID or tag for adding.", "error")
        return redirect(url_for('index'))

    row = query_db("SELECT tags FROM urls WHERE id = ?", [entry_id], one=True)
    if not row:
        flash("URL not found.", "error")
        return redirect(url_for('index'))

    old_tags = row['tags'] or ""
    tag_list = [t.strip() for t in old_tags.split(',') if t.strip()]
    if new_tag not in tag_list:
        tag_list.append(new_tag)
    updated_tags = ','.join(tag_list)

    execute_db("UPDATE urls SET tags = ? WHERE id = ?", [updated_tags, entry_id])
    flash(f"Added tag '{new_tag}' to entry {entry_id}.", "success")
    return redirect(url_for('index'))

@app.route('/bulk_action', methods=['POST'])
def bulk_action() -> Response:
    """Apply a bulk action (tag or delete) to selected URLs."""
    if not _db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    selected_ids = request.form.getlist('selected_ids')
    select_all_matching = (request.form.get('select_all_matching', 'false').lower() == 'true')

    if select_all_matching:
        q = request.form.get('q', '').strip()

        where_sql = ""
        params: List[str] = []
        if q:
            try:
                search_sql, params = search_utils.build_search_sql(q)
                where_sql = f"WHERE {search_sql}"
            except Exception:
                where_sql = (
                    "WHERE ("
                    "url LIKE ? OR tags LIKE ? OR "
                    "CAST(timestamp AS TEXT) LIKE ? OR "
                    "CAST(status_code AS TEXT) LIKE ? OR "
                    "mime_type LIKE ?"
                    ")"
                )
                params = [f"%{q}%"] * 5

        rows = query_db(f"SELECT id FROM urls {where_sql}", params)
        selected_ids = [str(r['id']) for r in rows]

    if not selected_ids:
        flash("No entries selected for bulk action.", "error")
        return redirect(url_for('index'))

    if action == 'add_tag':
        if not tag:
            flash("No tag provided for bulk add.", "error")
            return redirect(url_for('index'))
        count = 0
        for sid in selected_ids:
            row = query_db("SELECT tags FROM urls WHERE id = ?", [sid], one=True)
            if not row:
                continue
            old_tags = row['tags'] or ""
            tag_list = [t.strip() for t in old_tags.split(',') if t.strip()]
            if tag not in tag_list:
                tag_list.append(tag)
                updated_tags = ','.join(tag_list)
                execute_db("UPDATE urls SET tags = ? WHERE id = ?", [updated_tags, sid])
                count += 1
        flash(f"Added tag '{tag}' to {count} entries.", "success")

    elif action == 'remove_tag':
        if not tag:
            flash("No tag provided for removal.", "error")
            return redirect(url_for('index'))
        count = 0
        for sid in selected_ids:
            row = query_db("SELECT tags FROM urls WHERE id = ?", [sid], one=True)
            if not row:
                continue
            old_tags = row['tags'] or ""
            tag_list = [t.strip() for t in old_tags.split(',') if t.strip() and t.strip() != tag]
            updated_tags = ','.join(tag_list)
            execute_db("UPDATE urls SET tags = ? WHERE id = ?", [updated_tags, sid])
            count += 1
        flash(f"Removed tag '{tag}' from {count} entries.", "success")

    elif action == 'clear_tags':
        count = 0
        for sid in selected_ids:
            execute_db("UPDATE urls SET tags = '' WHERE id = ?", [sid])
            count += 1
        flash(f"Cleared tags from {count} entries.", "success")

    elif action == 'delete':
        count = 0
        for sid in selected_ids:
            execute_db("DELETE FROM urls WHERE id = ?", [sid])
            count += 1
        flash(f"Deleted {count} entries.", "success")

    else:
        flash(f"Unknown bulk action: {action}", "error")

    return redirect(url_for('index'))



from retrorecon.routes import (
    notes_bp,
    tools_bp,
    db_bp,
    settings_bp,
    domains_bp,
    docker_bp,
    oci_explorer_bp,
    dag_bp,
    oci_bp,
    dagdotdev_bp,
    urls_bp,
    swagger_bp,
    overview_bp,
    help_bp,
    dynamic_bp,
    chat_bp,
)
app.register_blueprint(notes_bp)
app.register_blueprint(tools_bp)
app.register_blueprint(db_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(domains_bp)
app.register_blueprint(docker_bp)
app.register_blueprint(oci_explorer_bp)
app.register_blueprint(dag_bp)
app.register_blueprint(oci_bp)
app.register_blueprint(dagdotdev_bp)
app.register_blueprint(urls_bp)
app.register_blueprint(swagger_bp)
app.register_blueprint(overview_bp)
app.register_blueprint(help_bp)
app.register_blueprint(dynamic_bp)
app.register_blueprint(chat_bp)



@app.after_request
def add_no_cache_headers(response: Response) -> Response:
    """Disable caching so templates always reload."""
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Pragma'] = 'no-cache'
    return response

if __name__ == '__main__':
    # Check if we're being run directly (not imported by launcher)
    if len(sys.argv) > 1 and sys.argv[1] == '--direct':
        # Direct mode - run without launcher setup
        if env_db and app.config.get('DATABASE'):
            with app.app_context():
                if not os.path.exists(app.config['DATABASE']):
                    create_new_db(os.path.splitext(os.path.basename(env_db))[0])
                else:
                    ensure_schema()
            app.mcp_server = start_mcp_sqlite(app.config['DATABASE'])
        host = os.environ.get('RETRORECON_LISTEN', '127.0.0.1')
        port = int(os.environ.get('RETRORECON_PORT', '5000'))
        app.run(debug=True, host=host, port=port)
    else:
        # Normal mode - use launcher for setup
        from retrorecon.launcher import main
        main()
