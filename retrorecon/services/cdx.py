import re
import urllib.parse
import requests
from typing import Tuple

from flask import current_app

from database import query_db, execute_db
from retrorecon import status as status_mod


def fetch_cdx(domain: str) -> int:
    """Fetch CDX entries for ``domain`` and insert new URLs. Returns count inserted."""
    cdx_api = (
        'http://web.archive.org/cdx/search/cdx'
        '?url={domain}/*&output=json&fl=original,timestamp,statuscode,mimetype'
        '&collapse=urlkey&limit=1000'
    ).format(domain=domain)

    status_mod.push_status('cdx_api_waiting', domain)
    status_mod.push_status('cdx_api_downloading', domain)
    resp = requests.get(cdx_api, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    status_mod.push_status('cdx_api_download_complete', domain)

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
            one=True,
        )
        if existing:
            continue
        entry_domain = urllib.parse.urlsplit(original_url).hostname or domain
        execute_db(
            "INSERT INTO urls (url, domain, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?, '')",
            [original_url, entry_domain, timestamp, status_code, mime_type],
        )
        inserted += 1
    status_mod.push_status('cdx_import_complete', str(inserted))
    return inserted
