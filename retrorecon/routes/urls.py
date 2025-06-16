import json
import os
import re
import sqlite3
import threading
import urllib.parse
import requests

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    session, jsonify, Response
)
from database import (
    query_db, execute_db, close_connection, ensure_schema, _sanitize_db_name
)
from retrorecon import search_utils
from retrorecon.services import (
    set_import_progress,
    get_import_progress,
    clear_import_progress,
)

bp = Blueprint('urls', __name__)


@bp.route('/', methods=['GET'])
def index() -> str:
    import app
    """Render the main search page."""
    q = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    tool = request.args.get('tool')
    if request.path == '/tools/jwt':
        tool = 'jwt'
    elif request.path == '/tools/screenshotter':
        tool = 'screenshot'

    sort = request.args.get('sort', 'id')
    direction = request.args.get('dir', 'desc').lower()
    if direction not in ['asc', 'desc']:
        direction = 'desc'

    try:
        items_per_page = int(session.get('items_per_page', app.ITEMS_PER_PAGE))
    except ValueError:
        items_per_page = app.ITEMS_PER_PAGE
    if items_per_page not in app.ITEMS_PER_PAGE_OPTIONS:
        items_per_page = app.ITEMS_PER_PAGE

    if app._db_loaded():
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

    if app._db_loaded():
        actual_name = os.path.basename(app.app.config['DATABASE'])
    else:
        actual_name = '(none)'
    if session.get('db_display_name') != actual_name:
        session['db_display_name'] = actual_name
    db_name = session['db_display_name']

    default_theme = 'nostalgia.css' if 'nostalgia.css' in app.AVAILABLE_THEMES else (app.AVAILABLE_THEMES[0] if app.AVAILABLE_THEMES else '')
    current_theme = session.get('theme', default_theme)

    default_background = 'background.jpg' if 'background.jpg' in app.AVAILABLE_BACKGROUNDS else (app.AVAILABLE_BACKGROUNDS[0] if app.AVAILABLE_BACKGROUNDS else '')
    current_background = session.get('background', default_background)

    panel_opacity = float(session.get('panel_opacity', 0.75))

    search_history = session.get('search_history', [])
    if q:
        if q in search_history:
            search_history.remove(q)
        search_history.insert(0, q)
        session['search_history'] = search_history[:10]

    return render_template(
        'index.html',
        urls=rows,
        page=page,
        total_pages=total_pages,
        q=q,
        themes=app.AVAILABLE_THEMES,
        theme_swatches=app.THEME_SWATCHES,
        current_theme=current_theme,
        backgrounds=app.AVAILABLE_BACKGROUNDS,
        current_background=current_background,
        panel_opacity=panel_opacity,
        total_count=total_count,
        items_per_page=items_per_page,
        db_name=db_name,
        search_history=search_history,
        current_sort=sort,
        current_dir=direction,
        open_tool=tool
    )


def _background_import(file_content: bytes) -> None:
    import app
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
        set_import_progress(app.IMPORT_PROGRESS_FILE, 'in_progress', '', 0, total)
        db = sqlite3.connect(app.app.config['DATABASE'])
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
                set_import_progress(app.IMPORT_PROGRESS_FILE, 'in_progress', '', idx + 1, total)
        db.commit()
        db.close()
        set_import_progress(app.IMPORT_PROGRESS_FILE, 'done', f"Imported {inserted} of {total} records.", inserted, total)
    except Exception as e:
        set_import_progress(app.IMPORT_PROGRESS_FILE, 'failed', str(e), 0, 0)


@bp.route('/fetch_cdx', methods=['POST'])
def fetch_cdx() -> Response:
    import app
    """Fetch CDX data for a domain and insert new URLs."""
    domain = request.form.get('domain', '').strip().lower()
    if not domain:
        flash("No domain provided for CDX fetch.", "error")
        return redirect(url_for('urls.index'))
    if not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
        flash("Invalid domain value.", "error")
        return redirect(url_for('urls.index'))
    if not app._db_loaded():
        flash("No database loaded.", "error")
        return redirect(url_for('urls.index'))

    cdx_api = (
        'http://web.archive.org/cdx/search/cdx'
        '?url={domain}/*&output=json&fl=original,timestamp,statuscode,mimetype'
        '&collapse=urlkey&limit=1000'
    ).format(domain=domain)

    try:
        resp = requests.get(cdx_api, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        flash(f"Error fetching CDX data: {e}", "error")
        return redirect(url_for('urls.index'))

    inserted = 0
    for idx, row in enumerate(data):
        if idx == 0:
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

    flash(f"Fetched CDX for {domain}: inserted {inserted} new URLs.", "success")
    return redirect(url_for('urls.index'))


@bp.route('/import_file', methods=['POST'])
@bp.route('/import_json', methods=['POST'])
def import_file() -> Response:
    import app
    """Import a JSON list or load a SQLite database depending on file type."""
    file = (
        request.files.get('import_file')
        or request.files.get('json_file')
        or request.files.get('db_file')
    )
    if not file:
        flash("No file uploaded for import.", "error")
        return redirect(url_for('urls.index'))

    filename = file.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext == 'json':
        if not app._db_loaded():
            flash("No database loaded.", "error")
            return redirect(url_for('urls.index'))
        clear_import_progress(app.IMPORT_PROGRESS_FILE)
        file_content = file.read()
        set_import_progress(app.IMPORT_PROGRESS_FILE, 'starting', 'Starting import...', 0, 0)
        thread = threading.Thread(target=_background_import, args=(file_content,))
        thread.start()
        flash("Import started! Progress will be shown below.", "success")
        return redirect(url_for('urls.index'))

    if ext == 'db':
        filename = _sanitize_db_name(filename)
        if not filename:
            flash('Invalid database file.', 'error')
            return redirect(url_for('urls.index'))
        db_path = os.path.join(app.app.root_path, filename)
        close_connection(None)
        try:
            file.save(db_path)
            app.app.config['DATABASE'] = db_path
            ensure_schema()
            session['db_display_name'] = filename
            flash("Database loaded.", "success")
        except Exception as e:
            flash(f"Error loading database: {e}", "error")
        return redirect(url_for('urls.index'))

    flash('Unsupported file type.', 'error')
    return redirect(url_for('urls.index'))


@bp.route('/import_progress', methods=['GET'])
def import_progress() -> Response:
    import app
    """Return JSON describing the current import progress."""
    prog = get_import_progress(app.IMPORT_PROGRESS_FILE)
    if request.args.get('clear') == '1' and prog.get('status') in ('done', 'failed'):
        clear_import_progress(app.IMPORT_PROGRESS_FILE)
    return jsonify({
        'status': prog.get('status', 'idle'),
        'progress': prog.get('current', 0),
        'total': prog.get('total', 0),
        'detail': prog.get('message', '')
    })


@bp.route('/add_tag', methods=['POST'])
def add_tag() -> Response:
    import app
    """Append a tag to the selected URL entry."""
    if not app._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('urls.index'))
    entry_id = request.form.get('entry_id')
    new_tag = request.form.get('new_tag', '').strip()
    if not entry_id or not new_tag:
        flash("Missing URL ID or tag for adding.", "error")
        return redirect(url_for('urls.index'))

    row = query_db("SELECT tags FROM urls WHERE id = ?", [entry_id], one=True)
    if not row:
        flash("URL not found.", "error")
        return redirect(url_for('urls.index'))

    old_tags = row['tags'] or ""
    tag_list = [t.strip() for t in old_tags.split(',') if t.strip()]
    if new_tag not in tag_list:
        tag_list.append(new_tag)
    updated_tags = ','.join(tag_list)

    execute_db("UPDATE urls SET tags = ? WHERE id = ?", [updated_tags, entry_id])
    flash(f"Added tag '{new_tag}' to entry {entry_id}.", "success")
    return redirect(url_for('urls.index'))


@bp.route('/bulk_action', methods=['POST'])
def bulk_action() -> Response:
    import app
    """Apply a bulk action (tag or delete) to selected URLs."""
    if not app._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('urls.index'))
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    selected_ids = request.form.getlist('selected_ids')
    select_all_matching = (request.form.get('select_all_matching', 'false').lower() == 'true')

    if select_all_matching:
        q = request.form.get('q', '').strip()

        where_clauses = []
        params = []
        if q:
            url_match = re.match(r'^url:"?(.*?)"?$', q, re.IGNORECASE)
            if url_match:
                val = url_match.group(1)
                where_clauses.append("url LIKE ?")
                params.append(f"%{val}%")
            elif '#' in q:
                tag_expr = search_utils.quote_hashtags(q)
                tag_expr = tag_expr.replace('#', '')
                try:
                    tag_sql, tag_params = search_utils.build_tag_filter_sql(tag_expr)
                    where_clauses.append(tag_sql)
                    params.extend(tag_params)
                except Exception:
                    where_clauses.append("tags LIKE ?")
                    params.append(f"%{tag_expr}%")
            else:
                where_clauses.append("("
                    "url LIKE ? OR tags LIKE ? OR "
                    "CAST(timestamp AS TEXT) LIKE ? OR "
                    "CAST(status_code AS TEXT) LIKE ?"
                ")")
                params.extend([f"%{q}%"] * 4)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        rows = query_db(f"SELECT id FROM urls {where_sql}", params)
        selected_ids = [str(r['id']) for r in rows]

    if not selected_ids:
        flash("No entries selected for bulk action.", "error")
        return redirect(url_for('urls.index'))

    if action == 'add_tag':
        if not tag:
            flash("No tag provided for bulk add.", "error")
            return redirect(url_for('urls.index'))
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
            return redirect(url_for('urls.index'))
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

    return redirect(url_for('urls.index'))
