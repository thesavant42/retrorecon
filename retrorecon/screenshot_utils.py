import os
import io
import base64
import logging
import socket
from urllib.parse import urlparse
from typing import Any, Dict, List, Optional, Tuple

import sqlite3
from database import execute_db, query_db

logger = logging.getLogger(__name__)


def save_record(
    dir_path: str,
    url: str,
    path: str,
    thumb: str,
    method: str = "GET",
    status_code: int = 0,
    ip_addresses: str = "",
) -> int:
    os.makedirs(dir_path, exist_ok=True)
    return execute_db(
        "INSERT INTO screenshots (url, method, screenshot_path, thumbnail_path, status_code, ip_addresses)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        [url, method, path, thumb, status_code, ip_addresses],
    )


def list_data(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    where = ""
    params: List[Any] = []
    if ids:
        placeholders = ",".join("?" for _ in ids)
        where = f"WHERE id IN ({placeholders})"
        params.extend(ids)
    rows = query_db(
        f"SELECT id, url, method, screenshot_path, thumbnail_path, status_code, ip_addresses, created_at"
        f" FROM screenshots {where} ORDER BY id DESC",
        params,
    )
    result = []
    for r in rows:
        result.append(
            {
                "id": r["id"],
                "url": r["url"],
                "method": r["method"],
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
            "SELECT screenshot_path, thumbnail_path FROM screenshots WHERE id = ?",
            [sid],
            one=True,
        )
        if row:
            file_path = os.path.join(dir_path, row["screenshot_path"])
            thumb_path = os.path.join(dir_path, row["thumbnail_path"])
            for fp in (file_path, thumb_path):
                try:
                    os.remove(fp)
                except OSError:
                    pass
        execute_db("DELETE FROM screenshots WHERE id = ?", [sid])


def resolve_ips(target_url: str) -> str:
    host = urlparse(target_url).hostname or ""
    if not host:
        return ""
    try:
        infos = socket.getaddrinfo(host, None)
        ips = {info[4][0] for info in infos}
        return ",".join(sorted(ips))
    except Exception:
        return ""


def take_screenshot(
    url: str,
    user_agent: str = "",
    spoof_referrer: bool = False,
    executable_path: Optional[str] = None,
    log_path: Optional[str] = None,
    har_path: Optional[str] = None,
) -> Tuple[bytes, int, str]:
    logger.debug("take_screenshot url=%s agent=%s spoof=%s", url, user_agent, spoof_referrer)
    ips = resolve_ips(url)
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        logger.debug("playwright not available: %s", e)
        return placeholder_image(url), 0, ips

    log_handler = None
    if log_path:
        log_handler = logging.FileHandler(log_path, encoding="utf-8")
        log_handler.setLevel(logging.DEBUG)
        logging.getLogger("playwright").addHandler(log_handler)
        logging.getLogger("playwright").setLevel(logging.DEBUG)
        logger.addHandler(log_handler)

    def _cap() -> Tuple[bytes, int]:
        launch_opts = {"args": ["--no-sandbox"]}
        exec_path = os.environ.get("PLAYWRIGHT_CHROMIUM_PATH") or executable_path
        if exec_path:
            launch_opts["executable_path"] = exec_path
            if "PLAYWRIGHT_CHROMIUM_PATH" in os.environ:
                logger.debug("using PLAYWRIGHT_CHROMIUM_PATH=%s", exec_path)
            else:
                logger.debug("using executable_path=%s", exec_path)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(**launch_opts)
                ctx_opts = {"ignore_https_errors": True}
                if user_agent:
                    ctx_opts["user_agent"] = user_agent
                if har_path:
                    ctx_opts["record_har_path"] = har_path
                    ctx_opts["record_har_content"] = "attach"
                context = browser.new_context(**ctx_opts)
                if spoof_referrer:
                    context.set_extra_http_headers({"Referer": url})
                page = context.new_page()
                # Avoid long hangs by waiting only for the load event with a
                # reasonable timeout. Some sites never reach a true
                # "networkidle" state which caused timeouts.
                response = page.goto(url, wait_until="load", timeout=15000)
                status = response.status if response else 0
                data = page.screenshot(full_page=True)
                context.close()
                browser.close()
                return data, status
        except Exception as e:
            logger.debug("screenshot capture failed: %s", e)
            raise

    try:
        img, status = _cap()
        return img, status, ips
    except Exception:
        return placeholder_image(url), 0, ips
    finally:
        if log_handler:
            logging.getLogger("playwright").removeHandler(log_handler)
            logger.removeHandler(log_handler)


def placeholder_image(text: str) -> bytes:
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (800, 600), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), text, fill="black")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except Exception:
        return base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8z8AAPAI" \
            "B+AWd1QAAAABJRU5ErkJggg=="
        )
