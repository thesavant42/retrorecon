import os
import re
from typing import List

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
    Response,
    send_from_directory,
    current_app,
)

from database import query_db, execute_db
from retrorecon import status as status_mod, search_utils
from retrorecon.filters import manifest_links, oci_obj
from ..services import (
    db_service,
    tags as tags_service,
    importer,
    cdx as cdx_service,
    urls as url_service,
)

bp = Blueprint('core', __name__)

bp.add_app_template_filter(manifest_links, name="manifest_links")
bp.add_app_template_filter(oci_obj, name="oci_obj")


@bp.route('/favicon.ico')
def favicon_ico() -> Response:
    return send_from_directory(bp.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@bp.route('/favicon.svg')
def favicon_svg() -> Response:
    return send_from_directory(bp.root_path, 'favicon.svg', mimetype='image/svg+xml')


@bp.route('/', methods=['GET'])
def index() -> str:
    repo_param = request.args.get('repo')
    image_param = request.args.get('image')
    if repo_param:
        from .oci import repo_view
        return repo_view(repo_param)
    if image_param:
        from .oci import image_view
        return image_view(image_param)

    q = request.args.get('q', '').strip()
    select_all_matching = request.args.get('select_all_matching', 'false').lower() == 'true'
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    tool = request.args.get('tool')
    if request.path == '/tools/jwt':
        tool = 'jwt'
    elif request.path == '/tools/screenshotter':
        tool = 'screenshot'
    elif request.path == '/tools/subdomonster':
        tool = 'subdomonster'
    elif request.path == '/tools/text_tools':
        tool = 'text'

    sort = request.args.get('sort', 'id')
    direction = request.args.get('dir', 'desc').lower()
    if direction not in ['asc', 'desc']:
        direction = 'desc'

    try:
        items_per_page = int(session.get('items_per_page', 10))
    except ValueError:
        items_per_page = 10
    if items_per_page not in [5, 10, 15, 20, 25]:
        items_per_page = 10

    if db_service.db_loaded():
        where_clauses = []
        params: List[str] = []
        if q:
            try:
                search_sql, search_params = search_utils.build_search_sql(q)
                where_clauses.append(search_sql)
                params.extend(search_params)
            except Exception:
                where_clauses.append(
                    "(" "url LIKE ? OR tags LIKE ? OR "
                    "CAST(timestamp AS TEXT) LIKE ? OR "
                    "CAST(status_code AS TEXT) LIKE ? OR "
                    "mime_type LIKE ?" ")"
                )
                params.extend([f"%{q}%"] * 5)
        where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        sort_map = {
            'url': 'url',
            'timestamp': 'timestamp',
            'status_code': 'status_code',
            'mime_type': 'mime_type',
            'id': 'id',
        }
        sort_col = sort_map.get(sort, 'id')

        count_sql = f"SELECT COUNT(*) AS cnt FROM urls {where_sql}"
        count_row = query_db(count_sql, params, one=True)
        total_count = count_row['cnt'] if count_row else 0

        total_pages = max(1, (total_count + items_per_page - 1) // items_per_page)

        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        offset = (page - 1) * items_per_page
        select_sql = f"""
            SELECT id, url, timestamp, status_code, mime_type, tags
            FROM urls
            {where_sql}
            ORDER BY {sort_col} {direction.upper()}
            LIMIT ? OFFSET ?
        """
        rows = query_db(select_sql, params + [items_per_page, offset])
    else:
        rows = []
        total_pages = 1
        total_count = 0

    if db_service.db_loaded():
        actual_name = os.path.basename(current_app.config['DATABASE'])
        if actual_name == db_service.TEMP_DB_NAME:
            actual_name = db_service.TEMP_DISPLAY_NAME
    else:
        actual_name = '(none)'
    if session.get('db_display_name') != actual_name:
        session['db_display_name'] = actual_name
    db_name = session['db_display_name']

    try:
        saved_dbs = sorted(
            [f for f in os.listdir(db_service.get_db_folder()) if f.endswith('.db') and os.path.isfile(os.path.join(db_service.get_db_folder(), f))]
        )
    except OSError:
        saved_dbs = []

    default_theme = 'nostalgia.css'
    current_theme = session.get('theme', default_theme)
    default_background = 'background.jpg'
    current_background = session.get('background', default_background)
    panel_opacity = float(session.get('panel_opacity', 0.75))

    search_history = session.get('search_history', [])
    if q:
        if q in search_history:
            search_history.remove(q)
        search_history.insert(0, q)
        session['search_history'] = search_history[:10]

    return render_template(
        'index.html',
        urls=rows,
        page=page,
        total_pages=total_pages,
        q=q,
        themes=[],
        theme_swatches={},
        current_theme=current_theme,
        backgrounds=[],
        current_background=current_background,
        panel_opacity=panel_opacity,
        total_count=total_count,
        items_per_page=items_per_page,
        db_name=db_name,
        saved_dbs=saved_dbs,
        search_history=search_history,
        current_sort=sort,
        current_dir=direction,
        open_tool=tool,
        select_all_matching=select_all_matching,
    )


@bp.route('/fetch_cdx', methods=['POST'])
def fetch_cdx_route() -> Response:
    domain = request.form.get('domain', '').strip().lower()
    if not domain:
        flash('No domain provided for CDX fetch.', 'error')
        return redirect(url_for('core.index'))
    if not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
        flash('Invalid domain value.', 'error')
        return redirect(url_for('core.index'))
    if not db_service.db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('core.index'))

    try:
        inserted = cdx_service.fetch_cdx(domain)
    except Exception as exc:  # pragma: no cover - network errors
        flash(f'Error fetching CDX data: {exc}', 'error')
        return redirect(url_for('core.index'))

    flash(f'Fetched CDX for {domain}: inserted {inserted} new URLs.', 'success')
    return redirect(url_for('core.index'))


@bp.route('/import_file', methods=['POST'])
@bp.route('/import_json', methods=['POST'])
def import_file_route() -> Response:
    file = request.files.get('import_file') or request.files.get('json_file')
    if not file:
        flash('No file uploaded for import.', 'error')
        return redirect(url_for('core.index'))
    filename = file.filename or ''
    if not filename.lower().endswith('.json'):
        flash('Please upload a JSON file.', 'error')
        return redirect(url_for('core.index'))
    if not db_service.db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('core.index'))
    importer.start_import(file.read())
    flash('Import started! Progress will be shown below.', 'success')
    return redirect(url_for('core.index'))


@bp.route('/import_progress', methods=['GET'])
def import_progress() -> Response:
    prog = importer.get_import_progress()
    if request.args.get('clear') == '1' and prog.get('status') in ('done', 'failed'):
        importer.clear_import_progress()
    return jsonify(
        {
            'status': prog.get('status', 'idle'),
            'progress': prog.get('current', 0),
            'total': prog.get('total', 0),
            'detail': prog.get('message', ''),
        }
    )


@bp.route('/status', methods=['GET'])
def status_route() -> Response:
    evt = status_mod.pop_status()
    last = evt
    while True:
        nxt = status_mod.pop_status()
        if not nxt:
            break
        last = nxt
    if not last:
        return ('', 204)
    return jsonify({'code': last[0], 'message': last[1]})


@bp.route('/add_tag', methods=['POST'])
def add_tag_route() -> Response:
    if not db_service.db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('core.index'))
    entry_id = request.form.get('entry_id')
    new_tag = request.form.get('new_tag', '').strip()
    if not entry_id or not new_tag:
        flash('Missing URL ID or tag for adding.', 'error')
        return redirect(url_for('core.index'))
    if url_service.add_tag(int(entry_id), new_tag):
        flash(f"Added tag '{new_tag}' to entry {entry_id}.", 'success')
    else:
        flash('URL not found.', 'error')
    return redirect(url_for('core.index'))


@bp.route('/bulk_action', methods=['POST'])
def bulk_action_route() -> Response:
    if not db_service.db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('core.index'))
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    selected_ids = request.form.getlist('selected_ids')
    select_all_matching = request.form.get('select_all_matching', 'false').lower() == 'true'

    if select_all_matching:
        q = request.form.get('q', '').strip()
        where_sql = ''
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
        flash('No entries selected for bulk action.', 'error')
        return redirect(url_for('core.index'))
    count = url_service.bulk_action(action, tag, selected_ids)
    flash(f'Updated {count} entries.', 'success')
    return redirect(url_for('core.index'))
