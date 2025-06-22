from typing import Dict, Any
import os
from flask import Blueprint, render_template, jsonify
import app

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
        row = app.query_db(f'SELECT COUNT(*) as cnt FROM {tbl}', one=True) if app._db_loaded() else None
        counts[tbl] = row['cnt'] if row else 0
    return counts


def _collect_domains() -> list:
    if not app._db_loaded():
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
