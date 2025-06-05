# File: app.py

import os
import io
import json
import sqlite3
import zipfile
import requests
from flask import (
    Flask, g, render_template, request,
    redirect, url_for, flash, send_file, session
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
# Path to your SQLite database (expects 'urls' table with columns: id, url, tags)
app.config['DATABASE'] = os.path.join(app.root_path, 'wabax.db')
# IMPORTANT: Replace this with a secure random key when deploying
app.secret_key = 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY'

# Pagination: how many URLs per page
ITEMS_PER_PAGE = 20

# Look for CSS theme files under static/themes/
THEMES_DIR = os.path.join(app.root_path, 'static', 'themes')
if os.path.isdir(THEMES_DIR):
    AVAILABLE_THEMES = sorted([f for f in os.listdir(THEMES_DIR) if f.endswith('.css')])
else:
    AVAILABLE_THEMES = []

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE INITIALIZATION (only if the file is missing)
# ─────────────────────────────────────────────────────────────────────────────

def init_db():
    """
    Initialize a SQLite database file with a 'urls' table
    containing (id INTEGER PRIMARY KEY, url TEXT NOT NULL, tags TEXT).
    """
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

# If the database file does not exist, create it and set up the table.
if not os.path.exists(app.config['DATABASE']):
    init_db()

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE CONNECTION HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_db():
    """
    Returns a SQLite connection (creating it if necessary) and stores it
    in the application context 'g'.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    """
    Closes the database connection at the end of the request, if open.
    """
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    """
    Helper to perform a SELECT query against the database.
    If one=True, returns a single row or None; otherwise returns a list of rows.
    """
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """
    Helper to execute INSERT/UPDATE/DELETE and commit immediately.
    Returns the lastrowid for INSERTs.
    """
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

# ─────────────────────────────────────────────────────────────────────────────
# INDEX ROUTE (HOME PAGE) 
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET'])
def index():
    """
    Renders the main page with a paginated list of URLs. Supports:
      - q: search substring in URL
      - tag: filter by exact tag
      - page: pagination
      - theme: chosen CSS theme (stored in session)
    """
    # Read filters from query params
    q = request.args.get('q', '').strip()
    tag_filter = request.args.get('tag', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    # Build WHERE clause based on search and tag
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

    # Count total matching rows for pagination
    count_sql = f"SELECT COUNT(*) AS cnt FROM urls {where_sql}"
    count_row = query_db(count_sql, params, one=True)
    total_count = count_row['cnt'] if count_row else 0
    total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

    # Clamp page into valid range
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    # Fetch rows for current page
    offset = (page - 1) * ITEMS_PER_PAGE
    select_sql = f"""
        SELECT id, url, tags
        FROM urls
        {where_sql}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """
    rows = query_db(select_sql, params + [ITEMS_PER_PAGE, offset])

    # Determine current theme (from session or default if not set)
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


# ─────────────────────────────────────────────────────────────────────────────
# FETCH CDX ROUTE (ONLY STORES 'url', NO 'timestamp' OR 'ext')
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/fetch_cdx', methods=['POST'])
def fetch_cdx():
    """
    Accepts a 'domain' from a form, queries the Wayback Machine CDX API,
    and inserts only the 'original URL' into the 'urls' table if not already present.
    """
    domain = request.form.get('domain', '').strip()
    if not domain:
        flash("No domain provided for CDX fetch.", "error")
        return redirect(url_for('index'))

    # Construct CDX API call: we request 'original' only (skip mimetype/timestamp)
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
            # Skip header row
            continue
        original_url = row[0]
        # Check if URL already exists
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


# ─────────────────────────────────────────────────────────────────────────────
# IMPORT NDJSON ROUTE (ONLY STORES 'url' AND OPTIONAL 'tags')
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/import_json', methods=['POST'])
def import_json():
    """
    Accepts an uploaded NDJSON file (one JSON object per line), each containing:
      { "url": "...", "tags": "..." }
    Inserts each record into the database (skipping duplicates).
    """
    file = request.files.get('json_file')
    if not file:
        flash("No file uploaded for NDJSON import.", "error")
        return redirect(url_for('index'))

    inserted = 0
    for raw_line in file.stream:
        line = raw_line.decode('utf-8').strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            url = record.get('url', '').strip()
            tags = record.get('tags', '').strip()
            if not url:
                continue
            # Skip duplicates
            existing = query_db(
                "SELECT id FROM urls WHERE url = ?",
                [url],
                one=True
            )
            if existing:
                continue
            execute_db(
                "INSERT INTO urls (url, tags) VALUES (?, ?)",
                [url, tags]
            )
            inserted += 1
        except json.JSONDecodeError:
            # Skip invalid JSON lines
            continue

    flash(f"Imported NDJSON: inserted {inserted} URLs.", "success")
    return redirect(url_for('index'))


# ─────────────────────────────────────────────────────────────────────────────
# ADD TAG ROUTE (SINGLE-ITEM TAGGING)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/add_tag', methods=['POST'])
def add_tag():
    """
    Adds a single tag to one URL record (specified by entry_id).
    """
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


# ─────────────────────────────────────────────────────────────────────────────
# BULK ACTION ROUTE (ADD/REMOVE TAGS, DELETE)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/bulk_action', methods=['POST'])
def bulk_action():
    """
    Performs bulk actions on selected URLs (add_tag, remove_tag, delete).
    Form fields:
      - action: 'add_tag' | 'remove_tag' | 'delete'
      - tag: tag to add/remove (if applicable)
      - selected_ids: list of URL IDs (checkboxes)
      - select_all_matching: "true" or "false" (if true, operate on all filtered results)
      - q, tag (filters) to re-select all matching when select_all_matching="true"
    """
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    selected_ids = request.form.getlist('selected_ids')
    select_all_matching = (request.form.get('select_all_matching', 'false').lower() == 'true')

    # If “Select all matching” is checked, re-fetch all filtered IDs
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


# ─────────────────────────────────────────────────────────────────────────────
# SET THEME ROUTE
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/set_theme', methods=['POST'])
def set_theme():
    """
    Allows the user to pick a CSS theme (from static/themes).
    Stores the choice in session and reloads the index.
    """
    theme = request.form.get('theme', '')
    if theme in AVAILABLE_THEMES:
        session['theme'] = theme
        flash(f"Theme changed to '{theme.replace('theme-', '').replace('.css', '').capitalize()}'", "success")
    else:
        flash("Invalid theme selection.", "error")
    return redirect(url_for('index'))


# ─────────────────────────────────────────────────────────────────────────────
# WEBPACK EXPLODER: ZIP‐CREATION ROUTE (No DB Changes)
# ─────────────────────────────────────────────────────────────────────────────

@app.route('/tools/webpack-zip', methods=['POST'])
def webpack_zip():
    """
    Fetches the .js.map JSON from the provided URL (map_url form field),
    bundles all inline sources into an in-memory ZIP, and returns it
    as a downloadable attachment. Flashes & redirects on error.
    """
    map_url = request.form.get('map_url', '').strip()
    if not map_url:
        flash("No .js.map URL provided.", "error")
        return redirect(url_for('index'))

    try:
        # 1) Download the .js.map text
        resp = requests.get(map_url, timeout=15)
        resp.raise_for_status()
        raw_text = resp.text

        # 2) Parse JSON
        map_data = json.loads(raw_text)

        # 3) Extract sources[] and sourcesContent[]
        sources = map_data.get('sources', [])
        sources_content = map_data.get('sourcesContent', [])

        # If lengths mismatch, warn and continue
        if len(sources_content) != len(sources):
            flash(
                "Warning: sourcesContent length does not match sources length. "
                "Some files may be skipped.",
                "warning"
            )

        # 4) Build an in-memory ZIP
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for idx, src_path in enumerate(sources):
                # Use the original src_path as filename inside ZIP
                filename_in_zip = src_path.replace('\\', '/').lstrip('/')
                if idx < len(sources_content) and sources_content[idx] is not None:
                    file_bytes = sources_content[idx].encode('utf-8')
                else:
                    # Skip if no inline content
                    continue
                zipf.writestr(filename_in_zip, file_bytes)

        zip_buffer.seek(0)

        # 5) Choose a ZIP filename based on the .js.map URL (replace .map → .zip)
        original_map_name = map_url.rstrip('/').split('/')[-1]
        zip_filename = original_map_name.replace('.map', '.zip')

        # 6) Send the ZIP as a download
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


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Ensure the database is initialized (if it doesn’t exist already)
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(debug=True)
