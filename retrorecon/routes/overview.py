from typing import Dict, Any
import os
from flask import Blueprint, jsonify
from .dynamic import dynamic_template
from retrorecon import subdomain_utils
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
    roots = app.query_db(
        'SELECT root_domain, COUNT(DISTINCT subdomain) AS cnt '
        'FROM domains GROUP BY root_domain ORDER BY root_domain'
    )
    domains = []
    for r in roots:
        rows = app.query_db(
            'SELECT subdomain, tags, cdx_indexed '
            'FROM domains WHERE root_domain = ? ORDER BY subdomain',
            [r['root_domain']]
        )
        seen = set()
        subs = []
        for row in rows:
            sub = subdomain_utils._clean(row['subdomain'])
            if sub in seen:
                continue
            seen.add(sub)
            subs.append(
                {
                    'subdomain': sub,
                    'tags': row['tags'],
                    'cdx_indexed': bool(row['cdx_indexed']),
                }
            )
        domains.append({
            'root_domain': subdomain_utils._clean(r['root_domain']),
            'count': r['cnt'],
            'subdomains': subs
        })
    return domains


@bp.route('/overview', methods=['GET'])
def overview_page():
    data = {
        'db_name': os.path.basename(app.app.config.get('DATABASE') or '(none)'),
        'counts': _collect_counts(),
        'domains': _collect_domains(),
    }
    return dynamic_template('overview.html', **data)


@bp.route('/overview.json', methods=['GET'])
def overview_json():
    data = {
        'db_name': os.path.basename(app.app.config.get('DATABASE') or '(none)'),
        'counts': _collect_counts(),
        'domains': _collect_domains(),
    }
    return jsonify(data)
