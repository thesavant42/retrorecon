import os
import io
import zipfile
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings

# Suppress warnings when capturing sites with invalid certificates
disable_warnings(InsecureRequestWarning)
from typing import Any, Dict, List, Optional, Tuple

from database import execute_db, query_db
from . import screenshot_utils


def save_record(
    dir_path: str,
    url: str,
    zip_path: str,
    screenshot_path: str,
    thumbnail_path: str,
    method: str = 'GET',
    status_code: int = 0,
    ip_addresses: str = '',
) -> int:
    os.makedirs(dir_path, exist_ok=True)
    return execute_db(
        "INSERT INTO sitezips (url, method, zip_path, screenshot_path, thumbnail_path, status_code, ip_addresses)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)",
        [url, method, zip_path, screenshot_path, thumbnail_path, status_code, ip_addresses],
    )


def list_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    where = ""
    params: List[Any] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        where = f"WHERE id IN ({placeholders})"
        params.extend(ids)
    rows = query_db(
        f"SELECT id, url, method, zip_path, screenshot_path, thumbnail_path, status_code, ip_addresses, created_at"
        f" FROM sitezips {where} ORDER BY id DESC",
        params,
    )
    result = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "url": r["url"],
                "method": r["method"],
                "zip_path": r["zip_path"],
                "screenshot_path": r["screenshot_path"],
                "thumbnail_path": r["thumbnail_path"],
                "status_code": r["status_code"],
                "ip_addresses": r["ip_addresses"],
                "created_at": r["created_at"],
            }
        )
    return result


def delete_records(dir_path: str, ids: List[int]) -> None:
    if not ids:
        return
    for sid in ids:
        row = query_db(
            "SELECT zip_path, screenshot_path, thumbnail_path FROM sitezips WHERE id = ?",
            [sid],
            one=True,
        )
        if row:
            for fname in (row["zip_path"], row["screenshot_path"], row["thumbnail_path"]):
                path = os.path.join(dir_path, fname)
                try:
                    os.remove(path)
                except OSError:
                    pass
        execute_db("DELETE FROM sitezips WHERE id = ?", [sid])


def capture_site(
    url: str,
    user_agent: str = '',
    spoof_referrer: bool = False,
    executable_path: Optional[str] = None,
) -> Tuple[bytes, bytes, int, str]:
    headers = {}
    if user_agent:
        headers['User-Agent'] = user_agent
    if spoof_referrer:
        headers['Referer'] = url
    resp = requests.get(url, headers=headers, timeout=15, verify=False)
    resp.raise_for_status()
    html = resp.text
    ip = ''
    try:
        ip = resp.raw._connection.sock.getpeername()[0]
    except Exception:
        pass
    screenshot, status, shot_ips = screenshot_utils.take_screenshot(
        url, user_agent, spoof_referrer, executable_path
    )
    if not ip:
        ip = shot_ips
    if status == 0:
        status = resp.status_code
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('index.html', html)
        z.writestr('screenshot.png', screenshot)
    buf.seek(0)
    return buf.getvalue(), screenshot, status, ip
