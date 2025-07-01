import logging
import re
import urllib.parse
import requests
from typing import List, Dict, Optional, Any
import tldextract

from database import execute_db, executemany_db, query_db, get_db

logger = logging.getLogger(__name__)

# Use a preconfigured TLDExtract instance that never performs network lookups
# and never writes cache files. This avoids delays from file locks or missing
# network access when ``scrape_from_urls`` tries to parse hostnames.
_EXTRACTOR = tldextract.TLDExtract(cache_dir=False, suffix_list_urls=())

# Regex to strip stray surrogate code points that break UTF-8 encoding
_SURROGATE_RE = re.compile('[\ud800-\udfff]')


def _clean(text: str) -> str:
    """Return ``text`` with any surrogate code points removed."""
    return _SURROGATE_RE.sub('', text)


def _merge_tags(tag_str: Optional[str]) -> str:
    """Return a deduplicated comma list from ``tag_str``."""
    if not tag_str:
        return ""
    tags: List[str] = []
    for t in tag_str.split(','):
        t = t.strip()
        if t and t not in tags:
            tags.append(t)
    return ','.join(tags)


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


def insert_records(
    root_domain: str,
    subs: List[str],
    source: str = "crtsh",
    cdx: bool = False,
) -> int:
    """Insert ``subs`` for ``root_domain`` and return count inserted."""
    params = [
        (_clean(root_domain), _clean(sub), source, "", int(cdx))
        for sub in subs
    ]
    try:
        return executemany_db(
            "INSERT OR IGNORE INTO domains (root_domain, subdomain, source, tags, cdx_indexed) VALUES (?, ?, ?, ?, ?)",
            params,
        )
    except Exception as exc:  # pragma: no cover - log only
        logger.debug("batch insert failed: %s", exc)
        count = 0
        for p in params:
            try:
                execute_db(
                    "INSERT OR IGNORE INTO domains (root_domain, subdomain, source, tags, cdx_indexed) VALUES (?, ?, ?, ?, ?)",
                    list(p),
                )
                count += 1
            except Exception as exc2:  # pragma: no cover - log only
                logger.debug("insert failed: %s", exc2)
        return count


def mark_cdxed(subdomain: str) -> None:
    """Mark a subdomain as indexed by CDX."""
    execute_db(
        "UPDATE domains SET cdx_indexed = 1 WHERE subdomain = ?",
        [_clean(subdomain)],
    )


def delete_record(root_domain: str, subdomain: str) -> None:
    """Remove ``subdomain`` for ``root_domain`` from the DB."""
    execute_db(
        "DELETE FROM domains WHERE root_domain = ? AND subdomain = ?",
        [_clean(root_domain), _clean(subdomain)],
    )


def update_record(
    root_domain: str, subdomain: str, new_root: str, new_sub: str
) -> None:
    """Rename ``subdomain`` and/or ``root_domain`` in the DB."""
    execute_db(
        "UPDATE domains SET root_domain = ?, subdomain = ?"
        " WHERE root_domain = ? AND subdomain = ?",
        [_clean(new_root), _clean(new_sub), _clean(root_domain), _clean(subdomain)],
    )


def add_tag(root_domain: str, subdomain: str, tag: str) -> None:
    rows = query_db(
        "SELECT id, tags FROM domains WHERE root_domain = ? AND subdomain = ?",
        [_clean(root_domain), _clean(subdomain)],
    )
    for r in rows:
        tag_list = [t.strip() for t in (r["tags"] or "").split(',') if t.strip()]
        if tag not in tag_list:
            tag_list.append(tag)
            execute_db(
                "UPDATE domains SET tags = ? WHERE id = ?",
                [','.join(tag_list), r["id"]],
            )


def remove_tag(root_domain: str, subdomain: str, tag: str) -> None:
    rows = query_db(
        "SELECT id, tags FROM domains WHERE root_domain = ? AND subdomain = ?",
        [_clean(root_domain), _clean(subdomain)],
    )
    for r in rows:
        tag_list = [
            t.strip()
            for t in (r["tags"] or "").split(',')
            if t.strip() and t.strip() != tag
        ]
        execute_db(
            "UPDATE domains SET tags = ? WHERE id = ?",
            [','.join(tag_list), r["id"]],
        )


def clear_tags(root_domain: str, subdomain: str) -> None:
    execute_db(
        "UPDATE domains SET tags = '' WHERE root_domain = ? AND subdomain = ?",
        [_clean(root_domain), _clean(subdomain)],
    )


def search_subdomains(term: str, root_domain: Optional[str] = None) -> List[Dict[str, str]]:
    """Return subdomains matching ``term`` in name or tags."""
    term = f"%{term.lower()}%"
    params: List[Any] = []
    where = "WHERE (d.subdomain LIKE ? OR d.tags LIKE ?)"
    params.extend([term, term])
    if root_domain:
        where += " AND d.root_domain = ?"
        params.append(_clean(root_domain))
    rows = query_db(
        f"""
        SELECT d.subdomain, d.root_domain as domain,
               GROUP_CONCAT(DISTINCT d.source) AS sources,
               GROUP_CONCAT(d.tags, ',') AS tags,
               MAX(d.cdx_indexed) AS cdxed,
               EXISTS(SELECT 1 FROM urls u WHERE u.domain = d.subdomain) AS in_urls
        FROM domains d
        {where}
        GROUP BY d.subdomain, d.root_domain
        ORDER BY d.subdomain
        """,
        params,
    )
    results = []
    for r in rows:
        indexed = r["cdxed"] or r["in_urls"]
        results.append(
            {
                "subdomain": _clean(r["subdomain"]),
                "domain": _clean(r["domain"]),
                "source": _clean(r["sources"]),
                "tags": _clean(_merge_tags(r["tags"])),
                "cdx_indexed": bool(indexed),
            }
        )
    return results


def list_subdomains(root_domain: str) -> List[Dict[str, str]]:
    """Return all subdomains for ``root_domain`` aggregated by source."""
    rows = query_db(
        """
        SELECT d.subdomain, d.root_domain as domain,
               GROUP_CONCAT(DISTINCT d.source) AS sources,
               GROUP_CONCAT(d.tags, ',') AS tags,
               MAX(d.cdx_indexed) AS cdxed,
               EXISTS(SELECT 1 FROM urls u WHERE u.domain = d.subdomain) AS in_urls
        FROM domains d
        WHERE d.root_domain = ?
        GROUP BY d.subdomain, d.root_domain
        ORDER BY d.subdomain
        """,
        [_clean(root_domain)],
    )
    results = []
    for r in rows:
        indexed = r["cdxed"] or r["in_urls"]
        results.append(
            {
                "subdomain": _clean(r["subdomain"]),
                "domain": _clean(r["domain"]),
                "source": _clean(r["sources"]),
                "tags": _clean(_merge_tags(r["tags"])),
                "cdx_indexed": bool(indexed),
            }
        )
    return results


def list_all_subdomains() -> List[Dict[str, str]]:
    """Return all subdomain records aggregated across all root domains."""
    rows = query_db(
        """
        SELECT d.subdomain, d.root_domain as domain,
               GROUP_CONCAT(DISTINCT d.source) AS sources,
               GROUP_CONCAT(d.tags, ',') AS tags,
               MAX(d.cdx_indexed) AS cdxed,
               EXISTS(SELECT 1 FROM urls u WHERE u.domain = d.subdomain) AS in_urls
        FROM domains d
        GROUP BY d.subdomain, d.root_domain
        ORDER BY d.subdomain
        """
    )
    results = []
    for r in rows:
        indexed = r["cdxed"] or r["in_urls"]
        results.append(
            {
                "subdomain": _clean(r["subdomain"]),
                "domain": _clean(r["domain"]),
                "source": _clean(r["sources"]),
                "tags": _clean(_merge_tags(r["tags"])),
                "cdx_indexed": bool(indexed),
            }
        )
    return results


def count_subdomains(root_domain: Optional[str] = None) -> int:
    """Return the number of unique subdomains for ``root_domain`` or all.

    This includes hosts referenced in the ``urls`` table so the count
    reflects every known subdomain, even if no explicit domain record
    exists for it.
    """
    hosts: set[str] = set()
    if root_domain:
        rows = query_db(
            "SELECT DISTINCT subdomain FROM domains WHERE root_domain = ?",
            [_clean(root_domain)],
        )
        hosts.update(_clean(r["subdomain"]) for r in rows)
        url_rows = query_db(
            "SELECT DISTINCT domain FROM urls WHERE domain = ? OR domain LIKE ?",
            [_clean(root_domain), f"%.{_clean(root_domain)}"],
        )
        hosts.update(_clean(r["domain"]) for r in url_rows if r["domain"])
    else:
        rows = query_db("SELECT DISTINCT subdomain FROM domains")
        hosts.update(_clean(r["subdomain"]) for r in rows)
        url_rows = query_db("SELECT DISTINCT domain FROM urls")
        hosts.update(_clean(r["domain"]) for r in url_rows if r["domain"])

    return len(hosts)


def list_subdomains_page(
    root_domain: Optional[str], offset: int, limit: int
) -> List[Dict[str, str]]:
    """Return subdomains for ``root_domain`` limited by ``offset``/``limit``."""
    params: List[Any] = []
    where = ""
    if root_domain:
        where = "WHERE d.root_domain = ?"
        params.append(_clean(root_domain))
    rows = query_db(
        f"""
        SELECT d.subdomain, d.root_domain as domain,
               GROUP_CONCAT(DISTINCT d.source) AS sources,
               GROUP_CONCAT(d.tags, ',') AS tags,
               MAX(d.cdx_indexed) AS cdxed,
               EXISTS(SELECT 1 FROM urls u WHERE u.domain = d.subdomain) AS in_urls
        FROM domains d
        {where}
        GROUP BY d.subdomain, d.root_domain
        ORDER BY d.subdomain
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    )
    results = []
    for r in rows:
        indexed = r["cdxed"] or r["in_urls"]
        results.append(
            {
                "subdomain": _clean(r["subdomain"]),
                "domain": _clean(r["domain"]),
                "source": _clean(r["sources"]),
                "tags": _clean(_merge_tags(r["tags"])),
                "cdx_indexed": bool(indexed),
            }
        )
    return results


def scrape_from_urls(target_root: Optional[str] = None) -> int:
    """Insert subdomains found in ``urls``. Return number inserted."""
    db = get_db()
    offset = 0
    limit = 500
    cache: Dict[str, str] = {}
    count = 0
    while True:
        if target_root:
            rows = db.execute(
                "SELECT DISTINCT url, domain FROM urls WHERE url LIKE ? OR domain = ? OR domain LIKE ? LIMIT ? OFFSET ?",
                (f"%{target_root}%", target_root, f"%.{target_root}", limit, offset),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT DISTINCT url, domain FROM urls LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        if not rows:
            break
        for r in rows:
            host = _clean((r["domain"] or "").lower())
            if not host:
                host = urllib.parse.urlsplit(r["url"]).hostname or ""
                host = _clean(host.lower())
            if not host:
                continue
            if target_root:
                root = _clean(target_root)
            else:
                root = cache.get(host)
                if not root:
                    ext = _EXTRACTOR(host)
                    root = f"{ext.domain}.{ext.suffix}" if ext.suffix else host
                    cache[host] = root
            count += insert_records(_clean(root), [_clean(host)], "scrape", cdx=True)
        offset += limit
    return count


def list_url_hosts() -> List[str]:
    """Return distinct hostnames from the ``urls`` table."""
    rows = query_db("SELECT url, domain FROM urls")
    hosts: List[str] = []
    for r in rows:
        host = (r["domain"] or "").lower().strip()
        if not host:
            host = urllib.parse.urlsplit(r["url"]).hostname or ""
            host = host.lower().strip()
        if host and host not in hosts:
            hosts.append(_clean(host))
    return hosts


def count_urls_for_host(host: str) -> int:
    """Return how many URL records are associated with ``host``."""
    row = query_db(
        "SELECT COUNT(*) AS cnt FROM urls WHERE domain = ?",
        [_clean(host)],
        one=True,
    )
    return row["cnt"] if row else 0


def count_urls_for_root(root: str) -> int:
    """Return total URL records for ``root`` and all its subdomains."""
    row = query_db(
        "SELECT COUNT(*) AS cnt FROM urls WHERE domain = ? OR domain LIKE ?",
        [_clean(root), f"%.{_clean(root)}"],
        one=True,
    )
    return row["cnt"] if row else 0
