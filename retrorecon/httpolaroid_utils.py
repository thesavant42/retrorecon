import os
import io
import zipfile
import hashlib
from urllib.parse import urlparse, urlunparse, urljoin
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from requests.packages.urllib3 import disable_warnings
import logging

# Suppress warnings when capturing sites with invalid certificates
disable_warnings(InsecureRequestWarning)
from typing import Any, Dict, List, Optional, Tuple

from database import execute_db, query_db
from . import screenshot_utils
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)


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
    log_path: Optional[str] = None,
    har_path: Optional[str] = None,
) -> Tuple[bytes, bytes, int, str]:
    headers = {}
    if user_agent:
        headers['User-Agent'] = user_agent
    if spoof_referrer:
        headers['Referer'] = url

    auth = None
    parsed = urlparse(url)
    if parsed.username or parsed.password:
        auth = (parsed.username or '', parsed.password or '')
        netloc = parsed.hostname or ''
        if parsed.port:
            netloc += f":{parsed.port}"
        url = urlunparse(parsed._replace(netloc=netloc, username=None, password=None))

    try:
        resp = requests.get(
            url,
            headers=headers,
            timeout=15,
            verify=False,
            allow_redirects=True,
            auth=auth,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.debug("initial request failed: %s", e)
        raise
    html = resp.text
    ip = ''
    try:
        ip = resp.raw._connection.sock.getpeername()[0]
    except Exception:
        pass
    screenshot, status, shot_ips = screenshot_utils.take_screenshot(
        resp.url,
        user_agent,
        spoof_referrer,
        executable_path,
        log_path,
        har_path,
    )
    if not ip:
        ip = shot_ips
    if status == 0:
        status = resp.status_code
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('index.html', html)
        z.writestr('screenshot.png', screenshot)
        req_headers = '\n'.join(f"{k}: {v}" for k, v in resp.request.headers.items())
        res_headers = '\n'.join(f"{k}: {v}" for k, v in resp.headers.items())
        z.writestr('request_headers.txt', req_headers)
        z.writestr('response_headers.txt', res_headers)
        if har_path and os.path.exists(har_path):
            try:
                with open(har_path, 'r', encoding='utf-8') as hf:
                    z.writestr('harlog.json', hf.read())
            except Exception:
                pass
        # Parse HTML for external JavaScript files and add them under assets/js
        try:
            soup = BeautifulSoup(html, 'html.parser')
            scripts = []
            for tag in soup.find_all('script', src=True):
                scripts.append(tag['src'])
            for tag in soup.find_all('link', rel=lambda v: v and 'preload' in v):
                if tag.get('as') == 'script' and tag.get('href'):
                    scripts.append(tag['href'])
            for idx, s in enumerate(scripts):
                js_url = urljoin(resp.url, s)
                try:
                    jresp = requests.get(
                        js_url,
                        headers=headers,
                        timeout=10,
                        verify=False,
                        allow_redirects=True,
                        auth=auth,
                    )
                    if jresp.status_code == 200 and jresp.content:
                        parsed_name = urlparse(js_url).path
                        name = os.path.basename(parsed_name) or f'script{idx}.js'
                        if not name.endswith('.js'):
                            name += '.js'
                        digest = hashlib.sha256(js_url.encode()).hexdigest()[:8]
                        fname = f'assets/js/{digest}_{name}'
                        z.writestr(fname, jresp.content)
                except Exception:
                    pass
        except Exception:
            pass
        # try fetching favicon
        try:
            fav_url = urljoin(resp.url, '/favicon.ico')
            fav_resp = requests.get(
                fav_url,
                headers=headers,
                timeout=10,
                verify=False,
                allow_redirects=True,
                auth=auth,
            )
            if fav_resp.status_code == 200 and fav_resp.content:
                z.writestr('favicon.ico', fav_resp.content)
        except Exception:
            pass
        meta = {
            'final_url': resp.url,
            'status_code': resp.status_code,
            'ip_addresses': ip,
        }
        z.writestr('meta.json', json.dumps(meta, indent=2))
    buf.seek(0)
    if har_path:
        try:
            os.remove(har_path)
        except OSError:
            pass
    return buf.getvalue(), screenshot, status, ip
