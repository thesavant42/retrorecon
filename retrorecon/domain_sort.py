"""Utilities for aggregating hostnames into a recursive domain tree."""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple
import urllib.parse


def _normalize_host(host: str) -> str:
    """Return a lowercased hostname without port or trailing dot."""
    host = host.strip().lower()
    if ":" in host:
        host = host.split(":", 1)[0]
    host = host.rstrip(".")
    return host


def extract_hosts(items: Iterable[str]) -> List[str]:
    """Return hostnames extracted from ``items`` which may be URLs or hosts."""
    hosts = []
    for item in items:
        item = item.strip()
        if not item:
            continue
        if "://" in item:
            host = urllib.parse.urlsplit(item).hostname or ""
        else:
            host = item
        host = _normalize_host(host)
        if host:
            hosts.append(host)
    return hosts


def aggregate_hosts(hosts: Iterable[str]) -> Dict[str, Any]:
    """Return a nested dictionary mapping subdomain parts to counts."""
    tree: Dict[str, Any] = {}
    for host in hosts:
        parts = [p for p in host.split(".") if p]
        if not parts:
            continue
        parts.reverse()
        node = tree
        for part in parts:
            entry = node.setdefault(part, {"_count": 0, "_children": {}})
            entry["_count"] += 1
            node = entry["_children"]
    return tree


def flatten_tree(tree: Dict[str, Any], prefix: List[str] | None = None) -> List[Tuple[str, int]]:
    """Return a list of ``(domain, count)`` paths from ``tree``."""
    prefix = prefix or []
    results: List[Tuple[str, int]] = []
    for label, data in tree.items():
        if not isinstance(data, dict):
            continue
        path_parts = list(reversed(prefix + [label]))
        domain = ".".join(path_parts)
        results.append((domain, data.get("_count", 0)))
        child = data.get("_children", {})
        results.extend(flatten_tree(child, prefix + [label]))
    return results
