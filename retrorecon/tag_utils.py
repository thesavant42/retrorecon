from typing import Iterable, List, Optional

from database import execute_db, query_db


def entry_exists(entry_id: int) -> bool:
    """Return True if a URL entry exists."""
    row = query_db("SELECT 1 FROM urls WHERE id = ?", [entry_id], one=True)
    return bool(row)


def _get_tag_list(tag_str: Optional[str]) -> List[str]:
    """Return a list of unique tags from a comma-separated string."""
    tags: List[str] = []
    if not tag_str:
        return tags
    for t in tag_str.split(','):
        t = t.strip()
        if t and t not in tags:
            tags.append(t)
    return tags


def _update_tags(entry_id: int, tags: List[str]) -> None:
    execute_db(
        "UPDATE urls SET tags = ? WHERE id = ?",
        [','.join(tags), entry_id],
    )


def add_tag(entry_id: int, tag: str) -> bool:
    """Add ``tag`` to the URL entry if not already present."""
    row = query_db("SELECT tags FROM urls WHERE id = ?", [entry_id], one=True)
    if not row:
        return False
    tags = _get_tag_list(row["tags"])
    if tag not in tags:
        tags.append(tag)
        _update_tags(entry_id, tags)
        return True
    return False


def remove_tag(entry_id: int, tag: str) -> bool:
    """Remove ``tag`` from the URL entry."""
    row = query_db("SELECT tags FROM urls WHERE id = ?", [entry_id], one=True)
    if not row:
        return False
    tags = [t for t in _get_tag_list(row["tags"]) if t != tag]
    _update_tags(entry_id, tags)
    return True


def clear_tags(entry_id: int) -> None:
    """Clear all tags from the URL entry."""
    _update_tags(entry_id, [])


def bulk_add_tag(ids: Iterable[int], tag: str) -> int:
    """Add ``tag`` to each URL entry in ``ids``. Return count updated."""
    count = 0
    for eid in ids:
        if add_tag(int(eid), tag):
            count += 1
    return count


def bulk_remove_tag(ids: Iterable[int], tag: str) -> int:
    """Remove ``tag`` from each URL entry in ``ids``. Return count updated."""
    count = 0
    for eid in ids:
        row = query_db("SELECT tags FROM urls WHERE id = ?", [eid], one=True)
        if not row:
            continue
        tags = [t for t in _get_tag_list(row["tags"]) if t != tag]
        _update_tags(int(eid), tags)
        count += 1
    return count


def bulk_clear_tags(ids: Iterable[int]) -> int:
    """Remove all tags from URL entries in ``ids``."""
    count = 0
    for eid in ids:
        _update_tags(int(eid), [])
        count += 1
    return count
