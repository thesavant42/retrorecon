import os
import threading
import urllib.parse
from typing import Any, Dict, List, Optional

from flask import current_app

from database import init_db, query_db, execute_db
from retrorecon import search_utils, subdomain_utils, import_utils

# Temporary database handling constants
TEMP_DB_NAME = 'temp.db'
TEMP_DISPLAY_NAME = 'UNSAVED'


def get_db_folder(root_path: Optional[str] = None) -> str:
    """Return the folder where database files are stored."""
    try:
        base = root_path or current_app.root_path
    except RuntimeError:
        if root_path is None:
            raise
        base = root_path
    folder = os.path.join(base, 'db')
    os.makedirs(folder, exist_ok=True)
    return folder


def _create_temp_db() -> None:
    """Create a fresh temporary database for this session."""
    current_app.config['DATABASE'] = os.path.join(get_db_folder(), TEMP_DB_NAME)
    if os.path.exists(current_app.config['DATABASE']):
        os.remove(current_app.config['DATABASE'])
    init_db()


def _db_loaded() -> bool:
    """Return True if a database file is currently configured and exists."""
    return bool(
        current_app.config.get('DATABASE') and os.path.exists(current_app.config['DATABASE'])
    )


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


def delete_subdomain(root_domain: str, subdomain: str) -> None:
    """Remove a subdomain entry from the database."""
    subdomain_utils.delete_record(root_domain, subdomain)


def _background_import(file_content: bytes, db_path: str, progress_file: str) -> None:
    """Background thread handler for JSON/line-delimited imports."""
    import_utils.background_import(file_content, db_path, progress_file)


def set_import_progress(progress_file: str, status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    import_utils.set_import_progress(progress_file, status, message, current, total)


def get_import_progress(progress_file: str) -> Dict[str, Any]:
    return import_utils.get_import_progress(progress_file)


def clear_import_progress(progress_file: str) -> None:
    import_utils.clear_import_progress(progress_file)
