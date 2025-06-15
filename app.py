import os
import io
import json
import sqlite3
import zipfile
import threading
import re
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import urllib.parse
from flask import (
    Flask,
    g,
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

app = Flask(__name__)
# Allow overriding the startup database via environment variable
env_db = os.environ.get('RETRORECON_DB')
if env_db:
    app.config['DATABASE'] = env_db if os.path.isabs(env_db) else os.path.join(app.root_path, env_db)
else:
    app.config['DATABASE'] = None
app.secret_key = 'CHANGE_THIS_TO_A_RANDOM_SECRET_KEY'
ITEMS_PER_PAGE = 20
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
IMPORT_LOCK = threading.Lock()
DEMO_DATA_FILE = os.path.join(app.root_path, 'data/demo_data.json')
SAVED_TAGS_FILE = os.path.join(app.root_path, 'saved_tags.json')
SAVED_TAGS_LOCK = threading.Lock()


def _db_loaded() -> bool:
    """Return True if a database file is currently configured and exists."""

    return bool(app.config.get('DATABASE') and os.path.exists(app.config['DATABASE']))

def set_import_progress(status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    """Write progress information to ``IMPORT_PROGRESS_FILE``."""
    with IMPORT_LOCK:
        progress = {
            'status': status,
            'message': message,
            'current': current,
            'total': total
        }
        with open(IMPORT_PROGRESS_FILE, 'w') as f:
            json.dump(progress, f)

def get_import_progress() -> Dict[str, Any]:
    """Return the current import progress state."""

    with IMPORT_LOCK:
        if not os.path.exists(IMPORT_PROGRESS_FILE):
            return {'status': 'idle', 'message': '', 'current': 0, 'total': 0}
        with open(IMPORT_PROGRESS_FILE, 'r') as f:
            return json.load(f)

def clear_import_progress() -> None:
    """Remove ``IMPORT_PROGRESS_FILE`` if it exists."""

    with IMPORT_LOCK:
        if os.path.exists(IMPORT_PROGRESS_FILE):
            os.remove(IMPORT_PROGRESS_FILE)


def load_saved_tags() -> List[str]:
    """Return the list of saved search tags."""

    with SAVED_TAGS_LOCK:
        if not os.path.exists(SAVED_TAGS_FILE):
            return []
        try:
            with open(SAVED_TAGS_FILE, 'r') as f:
                data = json.load(f)
            if isinstance(data, list):
                return [str(t) for t in data]
        except Exception:
            pass
        return []


def save_saved_tags(tags: List[str]) -> None:
    """Persist ``tags`` to ``SAVED_TAGS_FILE``."""

    with SAVED_TAGS_LOCK:
        with open(SAVED_TAGS_FILE, 'w') as f:
            json.dump(tags, f)


def get_notes(url_id: int) -> List[sqlite3.Row]:
    """Return all notes for a specific URL."""

    return query_db(
        "SELECT id, url_id, content, created_at, updated_at FROM notes WHERE url_id = ? ORDER BY id",
        [url_id],
    )


def add_note(url_id: int, content: str) -> int:
    """Insert a note and return the row id."""

    return execute_db(
        "INSERT INTO notes (url_id, content) VALUES (?, ?)",
        [url_id, escape(content)],
    )


def update_note(note_id: int, content: str) -> None:
    """Update an existing note."""

    execute_db(
        "UPDATE notes SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [escape(content), note_id],
    )


def delete_note_entry(note_id: int) -> None:
    """Delete a note by ID."""

    execute_db("DELETE FROM notes WHERE id = ?", [note_id])


def delete_all_notes(url_id: int) -> None:
    """Remove all notes for a URL."""

    execute_db("DELETE FROM notes WHERE url_id = ?", [url_id])


def export_notes_data() -> List[Dict[str, Any]]:
    """Return all notes grouped by URL."""

    rows = query_db(
        "SELECT urls.url, notes.content FROM notes JOIN urls ON notes.url_id = urls.id ORDER BY urls.url, notes.id"
    )
    grouped: Dict[str, List[str]] = {}
    for r in rows:
        grouped.setdefault(r["url"], []).append(r["content"])
    return [{"url": u, "notes": n} for u, n in grouped.items()]

def init_db() -> None:
    """Initialize the database using the schema.sql file."""
    schema_path = os.path.join(app.root_path, 'db', 'schema.sql')
    if not os.path.exists(schema_path):
        raise FileNotFoundError("schema.sql not found")
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = sqlite3.connect(app.config['DATABASE'])
    for statement in sql.split(';'):
        stmt = statement.strip()
        if stmt.upper().startswith("CREATE TABLE IF NOT EXISTS"):
            conn.execute(stmt)
    conn.commit()
    conn.close()

def ensure_schema() -> None:
    """Apply ``schema.sql`` to an existing database if tables are missing."""
    if os.path.exists(app.config['DATABASE']):
        init_db()

def load_demo_data() -> None:
    """Populate the database with entries from ``DEMO_DATA_FILE`` if present."""
    if not os.path.exists(DEMO_DATA_FILE):
        return
    try:
        with open(DEMO_DATA_FILE, 'r') as f:
            data = json.load(f)
    except Exception:
        return
    db = sqlite3.connect(app.config['DATABASE'])
    for rec in data:
        if isinstance(rec, dict):
            url = rec.get('url', '').strip()
            tags = rec.get('tags', '').strip()
        else:
            url = str(rec).strip()
            tags = ''
        if url:
            db.execute(
                "INSERT OR IGNORE INTO urls (url, tags) VALUES (?, ?)",
                (url, tags),
            )
    db.commit()
    db.close()

def _sanitize_db_name(name: str) -> Optional[str]:
    """Return a sanitized ``name.db`` or ``None`` if empty after cleaning."""

    base, _ = os.path.splitext(name)
    safe = re.sub(r"[^A-Za-z0-9_-]", "", base)[:64]
    if not safe:
        return None
    return safe + ".db"


def _sanitize_export_name(name: str) -> str:
    """Return a filename safe for download containing only allowed chars."""

    safe = re.sub(r"[^A-Za-z0-9_-]", "_", name.strip())
    safe = safe.strip("_") or "download"
    if not safe.lower().endswith(".db"):
        safe += ".db"
    return safe


def create_new_db(name: Optional[str] = None) -> str:
    """Reset the database and return the newly created filename."""
    nm = _sanitize_db_name(name) if name else 'waybax.db'
    if nm is None:
        raise ValueError('Invalid database name.')
    db_path = os.path.join(app.root_path, nm)
    if os.path.exists(db_path):
        os.remove(db_path)
    app.config['DATABASE'] = db_path
    init_db()
    # Databases used to include demo entries from ``data/demo_data.json``.
    # For production use we initialize an empty database.
    return nm

if app.config.get('DATABASE') and os.path.exists(app.config['DATABASE']):
    ensure_schema()


@app.before_request
def _update_display_name() -> None:
    """Ensure ``session['db_display_name']`` matches the current DB file."""
    if app.config.get('DATABASE'):
        actual_name = os.path.basename(app.config['DATABASE'])
    else:
        actual_name = '(none)'
    if session.get('db_display_name') != actual_name:
        session['db_display_name'] = actual_name

def get_db() -> sqlite3.Connection:
    """Return a SQLite connection stored on the Flask ``g`` object."""

    if not app.config.get('DATABASE'):
        raise RuntimeError('No database loaded.')
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        db.create_function('has_tag', 2, _has_tag)
    return db

@app.teardown_appcontext
def close_connection(exception: Optional[BaseException]) -> None:
    """Close the SQLite connection at app teardown and remove it from ``g``."""

    db = g.pop('_database', None)
    if db is not None:
        db.close()

def query_db(query: str, args: Union[Tuple, List] = (), one: bool = False) -> Any:
    """Execute ``query`` and return rows or a single row."""

    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query: str, args: Union[Tuple, List] = ()) -> int:
    """Execute ``query`` that modifies the DB and return ``lastrowid``."""

    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid


def _has_tag(tags: str, tag: str) -> int:
    """SQLite helper to check if ``tag`` exists in comma-separated ``tags``."""

    tag = tag.strip().lower()
    for t in tags.split(','):
        if t.strip().lower() == tag:
            return 1
    return 0


def _quote_hashtags(expr: str) -> str:
    """Surround bare hashtag terms with quotes for proper tokenization."""

    pattern = r'#([^#()]+?)(?=(?:\s+(?:AND|OR|NOT)\b|\s*\)|\s*#|$))'

    def repl(match: re.Match) -> str:
        inner = match.group(1).strip()
        if ' ' in inner and not (inner.startswith('"') and inner.endswith('"')):
            inner = f'"{inner}"'
        return f'tag:{inner}'

    return re.sub(pattern, repl, expr, flags=re.IGNORECASE)


def _tokenize_tag_expr(expr: str) -> List[str]:
    """Return a list of tokens for a boolean tag expression."""

    token_re = re.compile(
        r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|\"[^\"]+\"|[^\s()]+",
        re.IGNORECASE,
    )
    tokens = token_re.findall(expr)
    return [t.strip('"') for t in tokens]


def _parse_tag_expression(tokens: List[str], pos: int = 0) -> Tuple[str, List[str], int]:
    """Recursive descent parser returning SQL and params."""

    def parse_or(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_and(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'OR':
                p += 1
                rhs_sql, rhs_params, p = parse_and(p)
                sql = f"({sql} OR {rhs_sql})"
                params.extend(rhs_params)
            else:
                break
        return sql, params, p

    def parse_and(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_not(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'AND':
                p += 1
            elif t in ('OR', ')'):
                break
            else:
                # implicit AND
                pass
            rhs_sql, rhs_params, p = parse_not(p)
            sql = f"({sql} AND {rhs_sql})"
            params.extend(rhs_params)
        return sql, params, p

    def parse_not(p: int) -> Tuple[str, List[str], int]:
        if p < len(tokens) and tokens[p].upper() == 'NOT':
            p += 1
            sql, params, p = parse_not(p)
            return f"(NOT {sql})", params, p
        return parse_primary(p)

    def parse_primary(p: int) -> Tuple[str, List[str], int]:
        if p >= len(tokens):
            raise ValueError('Unexpected end of expression')
        tok = tokens[p]
        if tok == '(':  # parse subexpression
            sql, params, p = parse_or(p + 1)
            if p >= len(tokens) or tokens[p] != ')':
                raise ValueError('Unmatched parenthesis')
            return sql, params, p + 1
        if tok == ')':
            raise ValueError('Unexpected )')
        return "has_tag(tags, ?)", [tok], p + 1

    return parse_or(pos)


def build_tag_filter_sql(expr: str) -> Tuple[str, List[str]]:
    """Convert a boolean tag expression to a SQL fragment and parameters."""

    tokens = _tokenize_tag_expr(expr)
    sql, params, pos = _parse_tag_expression(tokens)
    if pos != len(tokens):
        raise ValueError('Invalid syntax')
    return sql, params


def _tokenize_search_expr(expr: str) -> List[str]:
    """Return a list of tokens for a general search expression."""

    token_re = re.compile(
        r"\(|\)|\bAND\b|\bOR\b|\bNOT\b|[a-zA-Z]+:\"[^\"]+\"|\"[^\"]+\"|[^\s()]+",
        re.IGNORECASE,
    )
    raw = token_re.findall(expr)
    tokens = []
    for t in raw:
        if ':' in t:
            prefix, rest = t.split(':', 1)
            if rest.startswith('"') and rest.endswith('"'):
                rest = rest[1:-1]
            tokens.append(f"{prefix}:{rest}")
        else:
            if t.startswith('"') and t.endswith('"'):
                t = t[1:-1]
            tokens.append(t)
    return tokens


def _parse_search_expression(tokens: List[str], pos: int = 0) -> Tuple[str, List[str], int]:
    """Recursive descent parser for general search expressions."""

    def parse_or(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_and(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'OR':
                p += 1
                rhs_sql, rhs_params, p = parse_and(p)
                sql = f"({sql} OR {rhs_sql})"
                params.extend(rhs_params)
            else:
                break
        return sql, params, p

    def parse_and(p: int) -> Tuple[str, List[str], int]:
        sql, params, p = parse_not(p)
        while p < len(tokens):
            t = tokens[p].upper()
            if t == 'AND':
                p += 1
            elif t in ('OR', ')'):
                break
            else:
                # implicit AND
                pass
            rhs_sql, rhs_params, p = parse_not(p)
            sql = f"({sql} AND {rhs_sql})"
            params.extend(rhs_params)
        return sql, params, p

    def parse_not(p: int) -> Tuple[str, List[str], int]:
        if p < len(tokens) and tokens[p].upper() == 'NOT':
            p += 1
            sql, params, p = parse_not(p)
            return f"(NOT {sql})", params, p
        return parse_primary(p)

    def term_sql(tok: str) -> Tuple[str, List[str]]:
        lower = tok.lower()
        if lower.startswith('url:'):
            val = tok[4:]
            return "url LIKE ?", [f"%{val}%"]
        if lower.startswith('timestamp:'):
            val = tok[len('timestamp:'):]
            return "CAST(timestamp AS TEXT) LIKE ?", [f"%{val}%"]
        if lower.startswith('http:'):
            val = tok[5:]
            return "CAST(status_code AS TEXT) LIKE ?", [f"%{val}%"]
        if lower.startswith('mime:'):
            val = tok[5:]
            return "mime_type LIKE ?", [f"%{val}%"]
        if lower.startswith('tag:'):
            return "has_tag(tags, ?)", [tok[4:]]
        return (
            "("
            "url LIKE ? OR tags LIKE ? OR CAST(timestamp AS TEXT) LIKE ? OR "
            "CAST(status_code AS TEXT) LIKE ? OR mime_type LIKE ?"
            ")",
            [f"%{tok}%"] * 5,
        )

    def parse_primary(p: int) -> Tuple[str, List[str], int]:
        if p >= len(tokens):
            raise ValueError('Unexpected end of expression')
        tok = tokens[p]
        if tok == '(':  # subexpression
            sql, params, p = parse_or(p + 1)
            if p >= len(tokens) or tokens[p] != ')':
                raise ValueError('Unmatched parenthesis')
            return sql, params, p + 1
        if tok == ')':
            raise ValueError('Unexpected )')
        sql, params = term_sql(tok)
        return sql, params, p + 1

    return parse_or(pos)


def build_search_sql(expr: str) -> Tuple[str, List[str]]:
    """Convert a search expression into SQL and parameters."""

    expr = _quote_hashtags(expr)
    tokens = _tokenize_search_expr(expr)
    sql, params, pos = _parse_search_expression(tokens)
    if pos != len(tokens):
        raise ValueError('Invalid syntax')
    return sql, params

@app.route('/', methods=['GET'])
def index() -> str:
    """Render the main search page."""
    q = request.args.get('q', '').strip()
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    sort = request.args.get('sort', 'id')
    direction = request.args.get('dir', 'desc').lower()
    if direction not in ['asc', 'desc']:
        direction = 'desc'

    if _db_loaded():
        where_clauses = []
        params = []
        if q:
            try:
                search_sql, search_params = build_search_sql(q)
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
        total_pages = max(1, (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)

        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        offset = (page - 1) * ITEMS_PER_PAGE
        select_sql = f"""
            SELECT id, url, timestamp, status_code, mime_type, tags
            FROM urls
            {where_sql}
            ORDER BY {sort_col} {direction.upper()}
            LIMIT ? OFFSET ?
        """
        rows = query_db(select_sql, params + [ITEMS_PER_PAGE, offset])
    else:
        rows = []
        total_pages = 1
        total_count = 0

    if _db_loaded():
        actual_name = os.path.basename(app.config['DATABASE'])
    else:
        actual_name = '(none)'
    if session.get('db_display_name') != actual_name:
        session['db_display_name'] = actual_name
    db_name = session['db_display_name']

    default_theme = 'nostalgia.css' if 'nostalgia.css' in AVAILABLE_THEMES else (AVAILABLE_THEMES[0] if AVAILABLE_THEMES else '')
    current_theme = session.get('theme', default_theme)

    default_background = 'background.jpg' if 'background.jpg' in AVAILABLE_BACKGROUNDS else (AVAILABLE_BACKGROUNDS[0] if AVAILABLE_BACKGROUNDS else '')
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
        themes=AVAILABLE_THEMES,
        theme_swatches=THEME_SWATCHES,
        current_theme=current_theme,
        backgrounds=AVAILABLE_BACKGROUNDS,
        current_background=current_background,
        panel_opacity=panel_opacity,
        total_count=total_count,
        db_name=db_name,
        search_history=search_history,
        current_sort=sort,
        current_dir=direction
    )

@app.route('/fetch_cdx', methods=['POST'])
def fetch_cdx() -> Response:
    """Fetch CDX data for a domain and insert new URLs."""
    domain = request.form.get('domain', '').strip()
    if not domain:
        flash("No domain provided for CDX fetch.", "error")
        return redirect(url_for('index'))
    if not _db_loaded():
        flash("No database loaded.", "error")
        return redirect(url_for('index'))

    cdx_api = (
        'http://web.archive.org/cdx/search/cdx'
        '?url={domain}/*&output=json&fl=original,timestamp,statuscode,mimetype&collapse=urlkey'
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
        execute_db(
            "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?)",
            [original_url, timestamp, status_code, mime_type, ""]
        )
        inserted += 1

    flash(f"Fetched CDX for {domain}: inserted {inserted} new URLs.", "success")
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
    """Import a JSON list or load a SQLite database depending on file type."""
    file = (
        request.files.get('import_file')
        or request.files.get('json_file')
        or request.files.get('db_file')
    )
    if not file:
        flash("No file uploaded for import.", "error")
        return redirect(url_for('index'))

    filename = file.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext == 'json':
        if not _db_loaded():
            flash("No database loaded.", "error")
            return redirect(url_for('index'))
        clear_import_progress()
        file_content = file.read()
        set_import_progress('starting', 'Starting import...', 0, 0)
        thread = threading.Thread(target=_background_import, args=(file_content,))
        thread.start()
        flash("Import started! Progress will be shown below.", "success")
        return redirect(url_for('index'))

    if ext == 'db':
        filename = _sanitize_db_name(filename)
        if not filename:
            flash('Invalid database file.', 'error')
            return redirect(url_for('index'))
        db_path = os.path.join(app.root_path, filename)
        close_connection(None)
        try:
            file.save(db_path)
            app.config['DATABASE'] = db_path
            ensure_schema()
            session['db_display_name'] = filename
            flash("Database loaded.", "success")
        except Exception as e:
            flash(f"Error loading database: {e}", "error")
        return redirect(url_for('index'))

    flash('Unsupported file type.', 'error')
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

        where_clauses = []
        params = []
        if q:
            url_match = re.match(r'^url:"?(.*?)"?$', q, re.IGNORECASE)
            if url_match:
                val = url_match.group(1)
                where_clauses.append("url LIKE ?")
                params.append(f"%{val}%")
            elif '#' in q:
                tag_expr = _quote_hashtags(q)
                tag_expr = tag_expr.replace('#', '')
                try:
                    tag_sql, tag_params = build_tag_filter_sql(tag_expr)
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

@app.route('/set_theme', methods=['POST'])
def set_theme() -> Response:
    """Store the selected theme in the session."""
    theme = request.form.get('theme', '')
    if theme in AVAILABLE_THEMES:
        session['theme'] = theme
        flash(f"Theme changed to '{theme.replace('theme-', '').replace('.css', '').capitalize()}'", "success")
    else:
        flash("Invalid theme selection.", "error")
    return redirect(url_for('index'))


@app.route('/set_background', methods=['POST'])
def set_background() -> Response:
    """Persist the selected background image in the session."""
    bg = request.form.get('background', '')
    if bg in AVAILABLE_BACKGROUNDS:
        session['background'] = bg
        return ('', 204)
    return ('Invalid background', 400)


@app.route('/set_panel_opacity', methods=['POST'])
def set_panel_opacity() -> Response:
    """Update and store the UI panel opacity setting."""
    try:
        opacity = float(request.form.get('opacity', '1'))
    except ValueError:
        return ('Invalid value', 400)
    opacity = max(0.1, min(opacity, 1.0))
    session['panel_opacity'] = opacity
    return ('', 204)


@app.route('/set_font_size', methods=['POST'])
def set_font_size() -> Response:
    """Update font size in the selected theme CSS file."""
    try:
        size = int(request.form.get('size', '14'))
    except ValueError:
        return ('Invalid value', 400)
    size = max(10, min(size, 18))
    theme = request.form.get('theme') or session.get('theme')
    if not theme and AVAILABLE_THEMES:
        theme = AVAILABLE_THEMES[0]
    if not theme or theme not in AVAILABLE_THEMES:
        return ('Invalid theme', 400)

    path = os.path.join(THEMES_DIR, theme)
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return ('Theme not found', 404)

    new_lines = []
    in_pagination = False
    in_footer = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('.retrorecon-root .pagination'):
            in_pagination = True
        elif stripped.startswith('.retrorecon-root .footer'):
            in_footer = True

        if 'font-size:' in line:
            if '13.333px' in line:
                line = re.sub(r'font-size:\s*[^;]+;', f'font-size: {size}px;', line)
            elif in_pagination or in_footer:
                line = re.sub(r'font-size:\s*[^;]+;', f'font-size: {size}px;', line)

        if in_pagination and '}' in line:
            in_pagination = False
        if in_footer and '}' in line:
            in_footer = False
        new_lines.append(line)

    with open(path, 'w') as fh:
        fh.write('\n'.join(new_lines) + '\n')
    return ('', 204)


@app.route('/saved_tags', methods=['GET', 'POST'])
def saved_tags() -> Response:
    """Return or update the list of saved search tags."""

    if request.method == 'GET':
        return jsonify({'tags': load_saved_tags()})

    tag = request.form.get('tag', '').strip()
    if not tag:
        return ('', 400)
    if not tag.startswith('#'):
        tag = '#' + tag
    tags = load_saved_tags()
    if tag not in tags:
        tags.append(tag)
        save_saved_tags(tags)
    return ('', 204)


@app.route('/delete_saved_tag', methods=['POST'])
def delete_saved_tag() -> Response:
    """Remove a tag from the saved list."""

    tag = request.form.get('tag', '').strip()
    if not tag:
        return ('', 400)
    if not tag.startswith('#'):
        tag = '#' + tag
    tags = load_saved_tags()
    if tag in tags:
        tags.remove(tag)
        save_saved_tags(tags)
    return ('', 204)


@app.route('/notes/<int:url_id>', methods=['GET'])
def notes_get(url_id: int) -> Response:
    """Return all notes for the given URL as JSON."""

    if not _db_loaded():
        return jsonify([])
    rows = get_notes(url_id)
    return jsonify([
        {
            'id': r['id'],
            'url_id': r['url_id'],
            'content': r['content'],
            'created_at': r['created_at'],
            'updated_at': r['updated_at'],
        }
        for r in rows
    ])


@app.route('/notes', methods=['POST'])
def notes_post() -> Response:
    """Create or update a note."""

    if not _db_loaded():
        return ('', 400)
    url_id = request.form.get('url_id', type=int)
    content = request.form.get('content', '').strip()
    if not url_id or not content:
        return ('', 400)
    note_id = request.form.get('note_id', type=int)
    if note_id:
        update_note(note_id, content)
    else:
        add_note(url_id, content)
    return ('', 204)


@app.route('/delete_note', methods=['POST'])
def delete_note_route() -> Response:
    """Delete a specific note or all notes for a URL."""

    note_id = request.form.get('note_id', type=int)
    url_id = request.form.get('url_id', type=int)
    delete_all = request.form.get('all', '0') == '1'
    if note_id:
        delete_note_entry(note_id)
    elif url_id and delete_all:
        delete_all_notes(url_id)
    else:
        return ('', 400)
    return ('', 204)


@app.route('/export_notes', methods=['GET'])
def export_notes() -> Response:
    """Return all notes as JSON grouped by URL."""

    if not _db_loaded():
        return jsonify([])
    data = export_notes_data()
    return jsonify(data)


@app.route('/text_tools', methods=['GET'])
def text_tools_page() -> str:
    """Return the Text Tools overlay HTML fragment."""

    return render_template('text_tools.html')


def _get_text_param() -> Optional[str]:
    text = request.form.get('text', '')
    if len(text.encode('utf-8')) > TEXT_TOOLS_LIMIT:
        return None
    return text


@app.route('/tools/base64_decode', methods=['POST'])
def base64_decode_route() -> Response:
    """Decode Base64 text."""

    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    import base64
    try:
        decoded = base64.b64decode(text, validate=True)
        decoded.decode('utf-8')  # ensure text only
    except Exception:
        return ('Invalid Base64 data', 400)
    return Response(decoded, mimetype='text/plain')


@app.route('/tools/base64_encode', methods=['POST'])
def base64_encode_route() -> Response:
    """Encode text as Base64."""

    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    import base64
    encoded = base64.b64encode(text.encode('utf-8')).decode('ascii')
    return Response(encoded, mimetype='text/plain')


@app.route('/tools/url_decode', methods=['POST'])
def url_decode_route() -> Response:
    """URL-decode percent-encoded text."""

    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    try:
        decoded = urllib.parse.unquote_plus(text)
    except Exception:
        return ('Invalid URL encoding', 400)
    return Response(decoded, mimetype='text/plain')


@app.route('/tools/url_encode', methods=['POST'])
def url_encode_route() -> Response:
    """Percent-encode text for URLs."""

    text = _get_text_param()
    if text is None:
        return ('Request too large', 400)
    encoded = urllib.parse.quote_plus(text)
    return Response(encoded, mimetype='text/plain')

@app.route('/tools/webpack-zip', methods=['POST'])
def webpack_zip() -> Response:
    """Package sources from a Webpack ``.map`` file into a ZIP archive."""
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

@app.route('/new_db', methods=['POST'])
def new_db() -> Response:
    """Create a fresh empty database."""
    name = request.form.get('db_name', '').strip()
    safe = _sanitize_db_name(name)
    if not safe:
        flash('Invalid database name.', 'error')
        return redirect(url_for('index'))
    close_connection(None)
    try:
        db_name = create_new_db(safe)
        session['db_display_name'] = db_name
        flash('New database created.', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))

@app.route('/load_db', methods=['POST'])
def load_db_route() -> Response:
    """Upload and load a database file provided by the user."""
    file = request.files.get('db_file')
    if not file:
        flash("No database file uploaded.", "error")
        return redirect(url_for('index'))
    filename = _sanitize_db_name(file.filename or '')
    if not filename:
        flash('Invalid database file.', 'error')
        return redirect(url_for('index'))
    db_path = os.path.join(app.root_path, filename)
    close_connection(None)
    try:
        file.save(db_path)
        app.config['DATABASE'] = db_path
        ensure_schema()
        session['db_display_name'] = filename
        flash("Database loaded.", "success")
    except Exception as e:
        flash(f"Error loading database: {e}", "error")
    return redirect(url_for('index'))

@app.route('/save_db', methods=['GET'])
def save_db() -> Response:
    """Return the database file for download."""

    if not _db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    name = request.args.get("name", "").strip()
    if name:
        safe_name = _sanitize_export_name(name)
    else:
        safe_name = os.path.basename(app.config["DATABASE"])
    return send_file(
        app.config['DATABASE'],
        as_attachment=True,
        download_name=safe_name
    )


@app.route('/rename_db', methods=['POST'])
def rename_db() -> Response:
    """Rename the current database file."""
    new_name = request.form.get('new_name', '').strip()
    safe = _sanitize_db_name(new_name or '')
    if not safe:
        flash('Invalid database name.', 'error')
        return redirect(url_for('index'))
    if not _db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    close_connection(None)
    new_path = os.path.join(app.root_path, safe)
    try:
        os.rename(app.config['DATABASE'], new_path)
    except OSError as e:
        flash(f'Error renaming database: {e}', 'error')
        return redirect(url_for('index'))
    app.config['DATABASE'] = new_path
    ensure_schema()
    session['db_display_name'] = safe
    flash('Database renamed.', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    if env_db and app.config.get('DATABASE'):
        if not os.path.exists(app.config['DATABASE']):
            create_new_db(os.path.splitext(os.path.basename(env_db))[0])
        else:
            ensure_schema()
    app.run(debug=True)
