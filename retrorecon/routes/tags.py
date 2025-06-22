from typing import List

import app
from flask import Blueprint, request, redirect, url_for, flash
from database import query_db, execute_db
from retrorecon import tag_utils, search_utils

bp = Blueprint('tags', __name__)


def load_saved_tags() -> List[str]:
    """Return saved tags from ``SAVED_TAGS_FILE``."""
    return app.saved_tags_mod.load_tags(app.SAVED_TAGS_FILE)


def save_saved_tags(tags: List[str]) -> None:
    """Persist ``tags`` to ``SAVED_TAGS_FILE``."""
    app.saved_tags_mod.save_tags(app.SAVED_TAGS_FILE, tags)


@bp.route('/add_tag', methods=['POST'])
def add_tag() -> "redirect":  # type: ignore[return-type]
    """Append a tag to the selected URL entry."""
    if not app._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    entry_id = request.form.get('entry_id', type=int)
    new_tag = request.form.get('new_tag', '').strip()
    if not entry_id or not new_tag:
        flash("Missing URL ID or tag for adding.", "error")
        return redirect(url_for('index'))

    if not tag_utils.entry_exists(entry_id):
        flash("URL not found.", "error")
        return redirect(url_for('index'))

    tag_utils.add_tag(entry_id, new_tag)
    flash(f"Added tag '{new_tag}' to entry {entry_id}.", "success")
    return redirect(url_for('index'))


@bp.route('/bulk_action', methods=['POST'])
def bulk_action() -> "redirect":  # type: ignore[return-type]
    """Apply a bulk action (tag or delete) to selected URLs."""
    if not app._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    selected_ids = request.form.getlist('selected_ids')
    select_all_matching = request.form.get('select_all_matching', 'false').lower() == 'true'

    if select_all_matching:
        q = request.form.get('q', '').strip()
        where_sql = ""
        params: List[str] = []
        if q:
            try:
                search_sql, params = search_utils.build_search_sql(q)
                where_sql = f"WHERE {search_sql}"
            except Exception:
                where_sql = (
                    "WHERE ("
                    "url LIKE ? OR tags LIKE ? OR "
                    "CAST(timestamp AS TEXT) LIKE ? OR "
                    "CAST(status_code AS TEXT) LIKE ? OR "
                    "mime_type LIKE ?"
                    ")"
                )
                params = [f"%{q}%"] * 5
        rows = query_db(f"SELECT id FROM urls {where_sql}", params)
        selected_ids = [str(r['id']) for r in rows]

    if not selected_ids:
        flash("No entries selected for bulk action.", "error")
        return redirect(url_for('index'))

    if action == 'add_tag':
        if not tag:
            flash("No tag provided for bulk add.", "error")
            return redirect(url_for('index'))
        count = tag_utils.bulk_add_tag([int(s) for s in selected_ids], tag)
        flash(f"Added tag '{tag}' to {count} entries.", "success")

    elif action == 'remove_tag':
        if not tag:
            flash("No tag provided for removal.", "error")
            return redirect(url_for('index'))
        count = tag_utils.bulk_remove_tag([int(s) for s in selected_ids], tag)
        flash(f"Removed tag '{tag}' from {count} entries.", "success")

    elif action == 'clear_tags':
        count = tag_utils.bulk_clear_tags([int(s) for s in selected_ids])
        flash(f"Cleared tags from {count} entries.", "success")

    elif action == 'delete':
        count = 0
        for sid in selected_ids:
            execute_db("DELETE FROM urls WHERE id = ?", [sid])
            count += 1
        flash(f"Deleted {count} entries.", "success")

    else:
        flash(f"Unknown bulk action: {action}", "error")

    return redirect(url_for('index'))

