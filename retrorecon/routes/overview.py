from typing import Dict, Any
import os
from flask import Blueprint, render_template, jsonify
import app
from retrorecon import app_utils

bp = Blueprint('overview', __name__)


def _collect_counts() -> Dict[str, int]:
    tables = [
        'urls',
        'domains',
        'screenshots',
        'sitezips',
        'jwt_cookies',
        'notes'
    ]
    counts = {}
    for tbl in tables:
        row = app.query_db(f'SELECT COUNT(*) as cnt FROM {tbl}', one=True) if app_utils._db_loaded() else None
        counts[tbl] = row['cnt'] if row else 0
    return counts


def _collect_domains() -> list:
    if not app_utils._db_loaded():
        return []
    roots = app.query_db('SELECT root_domain, COUNT(*) AS cnt FROM domains GROUP BY root_domain ORDER BY root_domain')
    domains = []
    for r in roots:
        rows = app.query_db(
            'SELECT subdomain, tags, cdx_indexed FROM domains WHERE root_domain = ? ORDER BY subdomain',
            [r['root_domain']]
        )
        subs = [
            {
                'subdomain': s['subdomain'],
                'tags': s['tags'],
                'cdx_indexed': bool(s['cdx_indexed'])
            }
            for s in rows
        ]
        domains.append({'root_domain': r['root_domain'], 'count': r['cnt'], 'subdomains': subs})
    return domains


@bp.route('/overview', methods=['GET'])
def overview_page():
    data = {
        'db_name': os.path.basename(app.app.config.get('DATABASE') or '(none)'),
        'counts': _collect_counts(),
        'domains': _collect_domains(),
    }
    return render_template('overview.html', **data)


@bp.route('/overview.json', methods=['GET'])
def overview_json():
    data = {
        'db_name': os.path.basename(app.app.config.get('DATABASE') or '(none)'),
        'counts': _collect_counts(),
        'domains': _collect_domains(),
    }
    return jsonify(data)

@bp.route('/', methods=['GET'])
def index() -> str:
    """Render the main search page or serve registry explorer views."""
    repo_param = app.request.args.get("repo")
    image_param = app.request.args.get("image")
    if repo_param:
        from retrorecon.routes.oci import repo_view
        return repo_view(repo_param)
    if image_param:
        from retrorecon.routes.oci import image_view
        return image_view(image_param)

    q = app.request.args.get('q', '').strip()
    is_tool_route = app.request.path in [
        '/tools/jwt',
        '/tools/screenshotter',
        '/tools/subdomonster',
        '/tools/text_tools'
    ]
    if not any([q, repo_param, image_param, app.request.args.get('tool'), is_tool_route]):
        if app_utils._db_loaded():
            actual_name = os.path.basename(app.app.config['DATABASE'])
            if actual_name == app.TEMP_DB_NAME:
                actual_name = app.TEMP_DISPLAY_NAME
        else:
            actual_name = '(none)'
        if app.session.get('db_display_name') != actual_name:
            app.session['db_display_name'] = actual_name
        db_name = app.session['db_display_name']
        default_theme = 'nostalgia.css' if 'nostalgia.css' in app.AVAILABLE_THEMES else (app.AVAILABLE_THEMES[0] if app.AVAILABLE_THEMES else '')
        current_theme = app.session.get('theme', default_theme)
        data = {
            'db_name': db_name,
            'counts': _collect_counts(),
            'domains': _collect_domains(),
            'current_theme': current_theme,
        }
        return render_template('overview.html', **data)

    select_all_matching = app.request.args.get('select_all_matching', 'false').lower() == 'true'
    try:
        page = int(app.request.args.get('page', 1))
    except ValueError:
        page = 1

    tool = app.request.args.get('tool')
    if app.request.path == '/tools/jwt':
        tool = 'jwt'
    elif app.request.path == '/tools/screenshotter':
        tool = 'screenshot'
    elif app.request.path == '/tools/subdomonster':
        tool = 'subdomonster'
    elif app.request.path == '/tools/text_tools':
        tool = 'text'

    sort = app.request.args.get('sort', 'id')
    direction = app.request.args.get('dir', 'desc').lower()
    if direction not in ['asc', 'desc']:
        direction = 'desc'

    try:
        items_per_page = int(app.session.get('items_per_page', app.ITEMS_PER_PAGE))
    except ValueError:
        items_per_page = app.ITEMS_PER_PAGE
    if items_per_page not in app.ITEMS_PER_PAGE_OPTIONS:
        items_per_page = app.ITEMS_PER_PAGE

    if app_utils._db_loaded():
        where_clauses = []
        params = []
        if q:
            try:
                search_sql, search_params = app.search_utils.build_search_sql(q)
                where_clauses.append(search_sql)
                params.extend(search_params)
            except Exception:
                where_clauses.append(
                    "(" "url LIKE ? OR tags LIKE ? OR " "CAST(timestamp AS TEXT) LIKE ? OR " "CAST(status_code AS TEXT) LIKE ? OR " "mime_type LIKE ?" ")"
                )
                params.extend([f"%{q}%"] * 5)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        sort_map = {
            'url': 'url',
            'timestamp': 'timestamp',
            'status_code': 'status_code',
            'mime_type': 'mime_type',
            'id': 'id'
        }
        sort_col = sort_map.get(sort, 'id')

        count_sql = f"SELECT COUNT(*) AS cnt FROM urls {where_sql}"
        count_row = app.query_db(count_sql, params, one=True)
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
        rows = app.query_db(select_sql, params + [items_per_page, offset])
    else:
        rows = []
        total_pages = 1
        total_count = 0

    if app_utils._db_loaded():
        actual_name = os.path.basename(app.app.config['DATABASE'])
        if actual_name == app.TEMP_DB_NAME:
            actual_name = app.TEMP_DISPLAY_NAME
    else:
        actual_name = '(none)'
    if app.session.get('db_display_name') != actual_name:
        app.session['db_display_name'] = actual_name
    db_name = app.session['db_display_name']

    try:
        saved_dbs = sorted([
            f for f in os.listdir(app_utils.get_db_folder())
            if f.endswith('.db') and os.path.isfile(os.path.join(app_utils.get_db_folder(), f))
        ])
    except OSError:
        saved_dbs = []

    default_theme = 'nostalgia.css' if 'nostalgia.css' in app.AVAILABLE_THEMES else (app.AVAILABLE_THEMES[0] if app.AVAILABLE_THEMES else '')
    current_theme = app.session.get('theme', default_theme)

    default_background = 'background.jpg' if 'background.jpg' in app.AVAILABLE_BACKGROUNDS else (app.AVAILABLE_BACKGROUNDS[0] if app.AVAILABLE_BACKGROUNDS else '')
    current_background = app.session.get('background', default_background)

    panel_opacity = float(app.session.get('panel_opacity', 0.75))

    search_history = app.session.get('search_history', [])
    if q:
        if q in search_history:
            search_history.remove(q)
        search_history.insert(0, q)
        app.session['search_history'] = search_history[:10]

    return render_template(
        'index.html',
        urls=rows,
        page=page,
        total_pages=total_pages,
        q=q,
        themes=app.AVAILABLE_THEMES,
        theme_swatches=app.THEME_SWATCHES,
        current_theme=current_theme,
        backgrounds=app.AVAILABLE_BACKGROUNDS,
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
        select_all_matching=select_all_matching
    )

@bp.route('/fetch_cdx', methods=['POST'])
def fetch_cdx() -> 'Response':
    """Fetch CDX data for a domain and insert new URLs."""
    domain = app.request.form.get('domain', '').strip().lower()
    if not domain:
        app.flash("No domain provided for CDX fetch.", "error")
        return app.redirect(app.url_for('overview.index'))
    if not re.match(r'^(?:[a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,63}$', domain):
        app.flash("Invalid domain value.", "error")
        return app.redirect(app.url_for('overview.index'))
    if not app_utils._db_loaded():
        app.flash("No database loaded.", "error")
        return app.redirect(app.url_for('overview.index'))

    cdx_api = (
        'http://web.archive.org/cdx/search/cdx'
        '?url={domain}/*&output=json&fl=original,timestamp,statuscode,mimetype'
        '&collapse=urlkey&limit=1000'
    ).format(domain=domain)

    app.status_mod.push_status('cdx_api_waiting', domain)
    try:
        app.status_mod.push_status('cdx_api_downloading', domain)
        resp = app.requests.get(cdx_api, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        app.status_mod.push_status('cdx_api_download_complete', domain)
    except Exception as e:
        app.flash(f"Error fetching CDX data: {e}", "error")
        return app.redirect(app.url_for('overview.index'))

    inserted = 0
    for idx, row in enumerate(data):
        if idx == 0:
            continue
        original_url = row[0]
        timestamp = row[1] if len(row) > 1 else None
        if len(row) > 2:
            status_raw = str(row[2])
            status_code = int(status_raw) if status_raw.isdigit() else None
        else:
            status_code = None
        mime_type = row[3] if len(row) > 3 else None
        existing = app.query_db(
            "SELECT id FROM urls WHERE url = ?",
            [original_url],
            one=True
        )
        if existing:
            continue
        entry_domain = urllib.parse.urlsplit(original_url).hostname or domain
        app.execute_db(
            "INSERT INTO urls (url, domain, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?, ?)",
            [original_url, entry_domain, timestamp, status_code, mime_type, ""]
        )
        inserted += 1

    app.flash(f"Fetched CDX for {domain}: inserted {inserted} new URLs.", "success")
    app.status_mod.push_status('cdx_import_complete', str(inserted))
    return app.redirect(app.url_for('overview.index'))
