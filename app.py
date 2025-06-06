import os
import io
import json
import sqlite3
import zipfile
import threading
import requests
from flask import (
    Flask, g, render_template, request,
    redirect, url_for, flash, send_file, session, jsonify
)

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.root_path, 'wabax.db')
app.secret_key = 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY'
ITEMS_PER_PAGE = 20

THEMES_DIR = os.path.join(app.root_path, 'static', 'themes')
if os.path.isdir(THEMES_DIR):
    AVAILABLE_THEMES = sorted([f for f in os.listdir(THEMES_DIR) if f.endswith('.css')])
else:
    AVAILABLE_THEMES = []

IMPORT_PROGRESS_FILE = os.path.join(app.root_path, 'import_progress.json')
IMPORT_LOCK = threading.Lock()

def set_import_progress(status, message='', current=0, total=0):
    with IMPORT_LOCK:
        progress = {
            'status': status,
            'message': message,
            'current': current,
            'total': total
        }
        with open(IMPORT_PROGRESS_FILE, 'w') as f:
            json.dump(progress, f)

def get_import_progress():
    with IMPORT_LOCK:
        if not os.path.exists(IMPORT_PROGRESS_FILE):
            return {'status': 'idle', 'message': '', 'current': 0, 'total': 0}
        with open(IMPORT_PROGRESS_FILE, 'r') as f:
            return json.load(f)

def clear_import_progress():
    with IMPORT_LOCK:
        if os.path.exists(IMPORT_PROGRESS_FILE):
            os.remove(IMPORT_PROGRESS_FILE)

def init_db():
    schema = """
    CREATE TABLE IF NOT EXISTS urls (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        url  TEXT NOT NULL,
        tags TEXT
    );
    """
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.executescript(schema)
    conn.close()

if not os.path.exists(app.config['DATABASE']):
    init_db()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

@app.route('/', methods=['GET'])
def index():
    q = request.args.get('q', '').strip()
    tag_filter = request.args.get('tag', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    where_clauses = []
    params = []
    if q:
        where_clauses.append("url LIKE ?")
        params.append(f"%{q}%")
    if tag_filter:
        where_clauses.append("tags LIKE ?")
        params.append(f"%{tag_filter}%")
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    count_sql = f"SELECT COUNT(*) AS cnt FROM urls {where_sql}"
    count_row = query_db(count_sql, params, one=True)
    total_count = count_row['cnt'] if count_row else 0
    total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    offset = (page - 1) * ITEMS_PER_PAGE
    select_sql = f"""
        SELECT id, url, tags
        FROM urls
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    rows = query_db(select_sql, params + [ITEMS_PER_PAGE, offset])

    current_theme = session.get('theme', AVAILABLE_THEMES[0] if AVAILABLE_THEMES else '')

    return render_template(
        'index.html',
        urls=rows,
        page=page,
        total_pages=total_pages,
        q=q,
        tag=tag_filter,
        themes=AVAILABLE_THEMES,
        current_theme=current_theme,
        total_count=total_count
    )

@app.route('/fetch_cdx', methods=['POST'])
def fetch_cdx():
    domain = request.form.get('domain', '').strip()
    if not domain:
        flash("No domain provided for CDX fetch.", "error")
        return redirect(url_for('index'))

    cdx_api = (
        'http://web.archive.org/cdx/search/cdx'
        '?url={domain}/*&output=json&fl=original&collapse=urlkey'
    ).format(domain=domain)

    try:
        resp = requests.get(cdx_api, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        flash(f"Error fetching CDX data: {e}", "error")
        return redirect(url_for('index'))

    inserted = 0
    for idx, row in enumerate(data):
        if idx == 0:
            continue
        original_url = row[0]
        existing = query_db(
            "SELECT id FROM urls WHERE url = ?",
            [original_url],
            one=True
        )
        if existing:
            continue
        execute_db(
            "INSERT INTO urls (url, tags) VALUES (?, ?)",
            [original_url, ""]
        )
        inserted += 1

    flash(f"Fetched CDX for {domain}: inserted {inserted} new URLs.", "success")
    return redirect(url_for('index'))

def _background_import(file_content):
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
                    {"url": rec.get('url', '').strip(), "tags": rec.get('tags', '').strip()}
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
                    tags = rec.get('tags', '').strip()
                    if url:
                        records.append({"url": url, "tags": tags})
                except Exception:
                    continue

        total = len(records)
        set_import_progress('in_progress', '', 0, total)
        db = sqlite3.connect(app.config['DATABASE'])
        c = db.cursor()
        inserted = 0
        for idx, rec in enumerate(records):
            try:
                c.execute("INSERT OR IGNORE INTO urls (url, tags) VALUES (?, ?)", (rec['url'], rec['tags']))
            except Exception:
                continue
            inserted += 1
            # Update progress every 10 or on last
            if idx % 10 == 0 or idx + 1 == total:
                set_import_progress('in_progress', '', idx + 1, total)
        db.commit()
        db.close()
        set_import_progress('done', '', total, total)
    except Exception as e:
        set_import_progress('failed', str(e), 0, 0)

@app.route('/import_json', methods=['POST'])
def import_json():
    file = request.files.get('json_file')
    if not file:
        flash("No file uploaded for import.", "error")
        return redirect(url_for('index'))

    clear_import_progress()
    file_content = file.read()
    set_import_progress('starting', 'Starting import...', 0, 0)

    thread = threading.Thread(target=_background_import, args=(file_content,))
    thread.start()

    flash("Import started! Progress will be shown below.", "success")
    return redirect(url_for('index'))

@app.route('/import_progress', methods=['GET'])
def import_progress():
    return jsonify({
        'status': 'in_progress',
        'progress': 500000,
        'total': 1000000,
        'detail': ''
    })

@app.route('/add_tag', methods=['POST'])
def add_tag():
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
def bulk_action():
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    selected_ids = request.form.getlist('selected_ids')
    select_all_matching = (request.form.get('select_all_matching', 'false').lower() == 'true')

    if select_all_matching:
        q = request.form.get('q', '').strip()
        tag_filter = request.form.get('tag', '').strip()

        where_clauses = []
        params = []
        if q:
            where_clauses.append("url LIKE ?")
            params.append(f"%{q}%")
        if tag_filter:
            where_clauses.append("tags LIKE ?")
            params.append(f"%{tag_filter}%")
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

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

    elif action == 'delete':
        count = 0
        for sid in selected_ids:
            execute_db("DELETE FROM urls WHERE id = ?", [sid])
            count += 1
        flash(f"Deleted {count} entries.", "success")

    else:
        flash(f"Unknown bulk action: {action}", "error")

    return redirect(url_for('index'))

@app.route('/set_theme', methods=['POST'])
def set_theme():
    theme = request.form.get('theme', '')
    if theme in AVAILABLE_THEMES:
        session['theme'] = theme
        flash(f"Theme changed to '{theme.replace('theme-', '').replace('.css', '').capitalize()}'", "success")
    else:
        flash("Invalid theme selection.", "error")
    return redirect(url_for('index'))

@app.route('/tools/webpack-zip', methods=['POST'])
def webpack_zip():
    map_url = request.form.get('map_url', '').strip()
    if not map_url:
        flash("No .js.map URL provided.", "error")
        return redirect(url_for('index'))

    try:
        resp = requests.get(map_url, timeout=15)
        resp.raise_for_status()
        raw_text = resp.text

        map_data = json.loads(raw_text)

        sources = map_data.get('sources', [])
        sources_content = map_data.get('sourcesContent', [])

        if len(sources_content) != len(sources):
            flash(
                "Warning: sourcesContent length does not match sources length. "
                "Some files may be skipped.",
                "warning"
            )

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, src_path in enumerate(sources):
                filename_in_zip = src_path.replace('\\', '/').lstrip('/')
                if idx < len(sources_content) and sources_content[idx] is not None:
                    file_bytes = sources_content[idx].encode('utf-8')
                else:
                    continue
                zipf.writestr(filename_in_zip, file_bytes)

        zip_buffer.seek(0)
        original_map_name = map_url.rstrip('/').split('/')[-1]
        zip_filename = original_map_name.replace('.map', '.zip')

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except requests.exceptions.RequestException as e:
        flash(f"Error fetching .js.map: {e}", "error")
        return redirect(url_for('index'))

    except (json.JSONDecodeError, KeyError) as e:
        flash(f"Error parsing .js.map JSON: {e}", "error")
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Unexpected server error: {e}", "error")
        return redirect(url_for('index'))

if __name__ == '__main__':
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(debug=True)