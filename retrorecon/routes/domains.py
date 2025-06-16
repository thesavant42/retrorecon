import re
from flask import Blueprint, request, jsonify, render_template
import app
from retrorecon import subdomain_utils

bp = Blueprint('domains', __name__)


@bp.route('/subdomonster', methods=['GET'])
def subdomonster_page():
    return render_template('subdomonster.html')


@bp.route('/tools/subdomonster', methods=['GET'])
def subdomonster_full_page():
    return app.index()


@bp.route('/subdomains', methods=['POST'])
def subdomains_route():
    if not app._db_loaded():
        return jsonify({'error': 'no_db'}), 400
    domain = request.form.get('domain', '').strip().lower()
    if not domain:
        return ('Missing domain', 400)
    if not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
        return ('Invalid domain', 400)
    try:
        subs = subdomain_utils.fetch_from_crtsh(domain)
    except Exception as e:  # pragma: no cover - network errors
        return (f'Error fetching: {e}', 500)
    subdomain_utils.insert_records(domain, subs, 'crtsh')
    return jsonify(subdomain_utils.list_subdomains(domain))
