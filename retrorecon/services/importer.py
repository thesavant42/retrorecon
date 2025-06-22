import json
import sqlite3
import threading
import sys
from typing import Any, Dict, List

from flask import current_app


def _progress_file() -> str:
    try:
        if current_app and 'IMPORT_PROGRESS_FILE' in current_app.config:
            return current_app.config['IMPORT_PROGRESS_FILE']
    except Exception:
        pass
    app_mod = sys.modules.get('app')
    return getattr(app_mod, 'IMPORT_PROGRESS_FILE', 'data/import_progress.json')


def _db_path() -> str:
    try:
        if current_app and 'DATABASE' in current_app.config:
            return current_app.config['DATABASE']
    except Exception:
        pass
    app_mod = sys.modules.get('app')
    return app_mod.app.config.get('DATABASE') if app_mod else ''

from retrorecon import progress as progress_mod, status as status_mod, search_utils


def set_import_progress(status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    progress_mod.set_progress(_progress_file(), status, message, current, total)


def get_import_progress() -> Dict[str, Any]:
    return progress_mod.get_progress(_progress_file())


def clear_import_progress() -> None:
    progress_mod.clear_progress(_progress_file())


def _background_import(file_content: bytes) -> None:
    """Background handler for JSON/line-delimited imports."""
    try:
        content = file_content.decode('utf-8').strip()
        records: List[Dict[str, Any]] = []
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
                        "tags": rec.get('tags', '').strip(),
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
                            "tags": rec.get('tags', '').strip(),
                        })
                except Exception:
                    continue
        total = len(records)
        set_import_progress('in_progress', '', 0, total)
        db = sqlite3.connect(_db_path())
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
                        rec['tags'],
                    ),
                )
            except Exception:
                continue
            inserted += 1
            if idx % 10 == 0 or idx + 1 == total:
                set_import_progress('in_progress', '', idx + 1, total)
        db.commit()
        db.close()
        set_import_progress('done', f"Imported {inserted} of {total} records.", inserted, total)
    except Exception as exc:  # pragma: no cover - log only
        set_import_progress('failed', str(exc), 0, 0)


def start_import(file_content: bytes) -> None:
    clear_import_progress()
    set_import_progress('starting', 'Starting import...', 0, 0)
    thread = threading.Thread(target=_background_import, args=(file_content,))
    thread.start()
