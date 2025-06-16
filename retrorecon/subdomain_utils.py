import logging
import requests
from typing import List, Dict

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


def list_subdomains(root_domain: str) -> List[Dict[str, str]]:
    """Return all subdomains for ``root_domain``."""
    rows = query_db(
        "SELECT subdomain, root_domain as domain, source FROM domains WHERE root_domain = ? ORDER BY subdomain",
        [root_domain],
    )
    return [
        {"subdomain": r["subdomain"], "domain": r["domain"], "source": r["source"]}
        for r in rows
    ]
