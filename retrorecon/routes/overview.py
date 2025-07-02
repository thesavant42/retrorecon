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

    roots = subdomain_utils.aggregate_root_domains()
    domains = []
    for root, subs in roots.items():
        rows = subdomain_utils.list_subdomains(root)
        domains.append(
            {
                'root_domain': root,
                'count': len(subs),
                'subdomains': [
                    {
                        'subdomain': r['subdomain'],
                        'tags': r['tags'],
                        'cdx_indexed': r['cdx_indexed'],
                    }
                    for r in rows
                ],
            }
        )
    domains.sort(key=lambda d: d['root_domain'])
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
