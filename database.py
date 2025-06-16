"""SQLite database helpers for Retrorecon."""

import os
import re
import sqlite3
from typing import Any, List, Optional, Tuple, Union

from flask import current_app, g


def _has_tag(tags: str, tag: str) -> int:
    """SQLite helper to check if ``tag`` exists in comma-separated ``tags``."""
    tag = tag.strip().lower()
    for t in tags.split(','):
        if t.strip().lower() == tag:
            return 1
    return 0


def init_db() -> None:
    """Initialize the database using the schema.sql file."""
    app = current_app
    schema_path = os.path.join(app.root_path, 'db', 'schema.sql')
    if not os.path.exists(schema_path):
        raise FileNotFoundError('schema.sql not found')
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql = f.read()
    conn = sqlite3.connect(app.config['DATABASE'])
    for statement in sql.split(';'):
        stmt = statement.strip()
        if stmt.upper().startswith('CREATE TABLE IF NOT EXISTS'):
            conn.execute(stmt)
    conn.commit()
    conn.close()


def ensure_schema() -> None:
    """Apply ``schema.sql`` to an existing database if tables are missing."""
    if os.path.exists(current_app.config['DATABASE']):
        init_db()
        # Add columns introduced in newer versions
        conn = sqlite3.connect(current_app.config['DATABASE'])
        try:
            cur = conn.execute("PRAGMA table_info(screenshots)")
            cols = [row[1] for row in cur.fetchall()]
            if 'thumbnail_path' not in cols:
                conn.execute("ALTER TABLE screenshots ADD COLUMN thumbnail_path TEXT")
            conn.commit()
        finally:
            conn.close()
        # Ensure the urls table has all expected columns
        ensure_url_columns()


def ensure_url_columns() -> None:
    """Add missing columns to the ``urls`` table if needed."""

    if os.path.exists(current_app.config['DATABASE']):
        conn = sqlite3.connect(current_app.config['DATABASE'])
        try:
            cur = conn.execute("PRAGMA table_info(urls)")
            cols = [row[1] for row in cur.fetchall()]
            required = {
                'domain': 'TEXT',
                'timestamp': 'TEXT',
                'status_code': 'INTEGER',
                'mime_type': 'TEXT',
                'tags': "TEXT DEFAULT ''",
            }
            for col, col_type in required.items():
                if col not in cols:
                    conn.execute(f"ALTER TABLE urls ADD COLUMN {col} {col_type}")
            conn.commit()
        finally:
            conn.close()


def _sanitize_db_name(name: str) -> Optional[str]:
    """Return a sanitized ``name.db`` or ``None`` if empty after cleaning."""
    base, _ = os.path.splitext(name)
    safe = re.sub(r"[^A-Za-z0-9_-]", "", base)[:64]
    if not safe:
        return None
    return safe + '.db'


def _sanitize_export_name(name: str) -> str:
    """Return a filename safe for download containing only allowed chars."""
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", name.strip())
    safe = safe.strip('_') or 'download'
    if not safe.lower().endswith('.db'):
        safe += '.db'
    return safe


def create_new_db(name: Optional[str] = None) -> str:
    """Reset the database and return the newly created filename."""
    nm = _sanitize_db_name(name) if name else 'waybax.db'
    if nm is None:
        raise ValueError('Invalid database name.')
    db_path = os.path.join(current_app.root_path, nm)
    if os.path.exists(db_path):
        os.remove(db_path)
    current_app.config['DATABASE'] = db_path
    init_db()
    return nm


def get_db() -> sqlite3.Connection:
    """Return a SQLite connection stored on the Flask ``g`` object."""
    if not current_app.config.get('DATABASE'):
        raise RuntimeError('No database loaded.')
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(current_app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        db.create_function('has_tag', 2, _has_tag)
    return db


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

