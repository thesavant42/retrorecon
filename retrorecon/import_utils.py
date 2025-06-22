import json
import sqlite3
from typing import Any, Dict, List

from . import progress as progress_mod


def set_import_progress(file_path: str, status: str, message: str = '', current: int = 0, total: int = 0) -> None:
    """Write progress information to ``file_path``."""
    progress_mod.set_progress(file_path, status, message, current, total)


def get_import_progress(file_path: str) -> Dict[str, Any]:
    """Return import progress stored at ``file_path``."""
    return progress_mod.get_progress(file_path)


def clear_import_progress(file_path: str) -> None:
    """Remove the progress file if it exists."""
    progress_mod.clear_progress(file_path)


def background_import(file_content: bytes, db_path: str, progress_file: str) -> None:
    """Import JSON records into the database and update progress."""
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
                        "url": rec.get("url", "").strip(),
                        "timestamp": rec.get("timestamp"),
                        "status_code": rec.get("status_code"),
                        "mime_type": rec.get("mime_type"),
                        "tags": rec.get("tags", "").strip(),
                    }
                    for rec in data
                    if rec.get("url", "").strip()
                ]
        except Exception:
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    url = rec.get("url", "").strip()
                    if url:
                        records.append(
                            {
                                "url": url,
                                "timestamp": rec.get("timestamp"),
                                "status_code": rec.get("status_code"),
                                "mime_type": rec.get("mime_type"),
                                "tags": rec.get("tags", "").strip(),
                            }
                        )
                except Exception:
                    continue
        total = len(records)
        set_import_progress(progress_file, 'in_progress', '', 0, total)
        db = sqlite3.connect(db_path)
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
                set_import_progress(progress_file, 'in_progress', '', idx + 1, total)
        db.commit()
        db.close()
        set_import_progress(progress_file, 'done', f"Imported {inserted} of {total} records.", inserted, total)
    except Exception as e:  # pragma: no cover - should not happen normally
        set_import_progress(progress_file, 'failed', str(e), 0, 0)
