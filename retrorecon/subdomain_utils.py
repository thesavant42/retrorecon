import logging
import requests
from typing import List, Dict, Optional

from database import execute_db, query_db

logger = logging.getLogger(__name__)


def fetch_from_crtsh(domain: str) -> List[str]:
    """Return subdomains for *domain* fetched from crt.sh."""
    url = f"https://crt.sh/json?identity={domain}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    subs = set()
    for entry in data:
        values = [entry.get("common_name", ""), entry.get("name_value", "")]
        for field in values:
            for name in str(field).replace("\\n", "\n").splitlines():
                name = name.strip().lower()
                if not name or "*" in name:
                    continue
                subs.add(name)
    return sorted(subs)


def fetch_from_virustotal(domain: str, api_key: str) -> List[str]:
    """Return subdomains for *domain* fetched from the VirusTotal API."""
    url = f"https://www.virustotal.com/api/v3/domains/{domain}/subdomains?limit=40"
    headers = {"x-apikey": api_key}
    subs = []
    while url:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        subs.extend([d.get("id", "").lower() for d in data.get("data", [])])
        url = data.get("links", {}).get("next")
    return sorted(set(s for s in subs if s))


def insert_records(root_domain: str, subs: List[str], source: str = "crtsh") -> int:
    """Insert ``subs`` for ``root_domain`` and return count inserted."""
    count = 0
    for sub in subs:
        try:
            execute_db(
                "INSERT OR IGNORE INTO domains (root_domain, subdomain, source) VALUES (?, ?, ?)",
                [root_domain, sub, source],
            )
            count += 1
        except Exception as exc:  # pragma: no cover - log only
            logger.debug("insert failed: %s", exc)
    return count


def mark_cdxed(subdomain: str) -> None:
    """Mark a subdomain as indexed by CDX."""
    execute_db(
        "UPDATE domains SET cdx_indexed = 1 WHERE subdomain = ?",
        [subdomain],
    )


def delete_record(root_domain: str, subdomain: str) -> None:
    """Remove ``subdomain`` for ``root_domain`` from the DB."""
    execute_db(
        "DELETE FROM domains WHERE root_domain = ? AND subdomain = ?",
        [root_domain, subdomain],
    )


def list_subdomains(root_domain: str) -> List[Dict[str, str]]:
    """Return all subdomains for ``root_domain``."""
    rows = query_db(
        """
        SELECT d.subdomain, d.root_domain as domain, d.source, d.cdx_indexed,
               EXISTS(SELECT 1 FROM urls u WHERE u.domain = d.subdomain) AS in_urls
        FROM domains d WHERE d.root_domain = ? ORDER BY d.subdomain
        """,
        [root_domain],
    )
    results = []
    for r in rows:
        indexed = r["cdx_indexed"] or r["in_urls"]
        results.append(
            {
                "subdomain": r["subdomain"],
                "domain": r["domain"],
                "source": r["source"],
                "cdx_indexed": bool(indexed),
            }
        )
    return results


def scrape_from_urls(target_root: Optional[str] = None) -> int:
    """Insert subdomains found in ``urls``. Return number inserted."""
    if target_root:
        rows = query_db(
            "SELECT DISTINCT domain FROM urls WHERE domain = ? OR domain LIKE ?",
            [target_root, f'%.{target_root}'],
        )
    else:
        rows = query_db("SELECT DISTINCT domain FROM urls")

    count = 0
    for r in rows:
        host = (r["domain"] or "").lower()
        if not host:
            continue
        if target_root:
            root = target_root
        else:
            parts = host.split(".")
            root = ".".join(parts[-2:]) if len(parts) >= 2 else host
        count += insert_records(root, [host], "scrape")
    return count
