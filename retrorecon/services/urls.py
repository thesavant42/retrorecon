import re
from typing import Any, Dict, List, Optional

from database import query_db, execute_db
from retrorecon import search_utils


def export_url_data(ids: Optional[List[int]] = None, query: str = '') -> List[Dict[str, Any]]:
    """Return URL records filtered by IDs or search query."""
    where = []
    params: List[Any] = []
    if ids:
        placeholders = ','.join('?' for _ in ids)
        where.append(f'id IN ({placeholders})')
        params.extend(ids)
    if query:
        try:
            search_sql, search_params = search_utils.build_search_sql(query)
            where.append(search_sql)
            params.extend(search_params)
        except Exception:
            where.append(
                '('
                'url LIKE ? OR tags LIKE ? OR '
                'CAST(timestamp AS TEXT) LIKE ? OR '
                'CAST(status_code AS TEXT) LIKE ? OR '
                'mime_type LIKE ?'
                ')'
            )
            params.extend([f'%{query}%'] * 5)
    where_sql = 'WHERE ' + ' AND '.join(where) if where else ''
    rows = query_db(
        f"SELECT id, url, timestamp, status_code, mime_type, tags FROM urls {where_sql} ORDER BY id",
        params,
    )
    result = []
    for r in rows:
        result.append(
            {
                'id': r['id'],
                'url': r['url'],
                'timestamp': r['timestamp'],
                'status_code': r['status_code'],
                'mime_type': r['mime_type'],
                'tags': r['tags'],
            }
        )
    return result


def add_tag(entry_id: int, new_tag: str) -> bool:
    row = query_db("SELECT tags FROM urls WHERE id = ?", [entry_id], one=True)
    if not row:
        return False
    old_tags = row['tags'] or ''
    tag_list = [t.strip() for t in old_tags.split(',') if t.strip()]
    if new_tag not in tag_list:
        tag_list.append(new_tag)
    updated = ','.join(tag_list)
    execute_db("UPDATE urls SET tags = ? WHERE id = ?", [updated, entry_id])
    return True


def bulk_action(action: str, tag: str, selected_ids: List[str]) -> int:
    count = 0
    if action == 'add_tag':
        for sid in selected_ids:
            if add_tag(int(sid), tag):
                count += 1
    elif action == 'remove_tag':
        for sid in selected_ids:
            row = query_db("SELECT tags FROM urls WHERE id = ?", [sid], one=True)
            if not row:
                continue
            old_tags = row['tags'] or ''
            tag_list = [t.strip() for t in old_tags.split(',') if t.strip() and t.strip() != tag]
            execute_db("UPDATE urls SET tags = ? WHERE id = ?", [','.join(tag_list), sid])
            count += 1
    elif action == 'clear_tags':
        for sid in selected_ids:
            execute_db("UPDATE urls SET tags = '' WHERE id = ?", [sid])
            count += 1
    elif action == 'delete':
        for sid in selected_ids:
            execute_db("DELETE FROM urls WHERE id = ?", [sid])
            count += 1
    return count
