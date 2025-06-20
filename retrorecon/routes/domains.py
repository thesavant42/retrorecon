import io
import csv
import re
from flask import Blueprint, request, jsonify, render_template, Response
import app
from retrorecon import subdomain_utils
from typing import Optional

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
    source = request.form.get('source', 'crtsh')
    api_key = request.form.get('api_key', '').strip()
    try:
        if source == 'virustotal':
            if not api_key:
                return ('Missing API key', 400)
            subs = subdomain_utils.fetch_from_virustotal(domain, api_key)
        else:
            subs = subdomain_utils.fetch_from_crtsh(domain)
    except Exception as e:  # pragma: no cover - network errors
        return (f'Error fetching: {e}', 500)
    subdomain_utils.insert_records(domain, subs, source)
    return jsonify(subdomain_utils.list_subdomains(domain))


@bp.route('/export_subdomains', methods=['GET'])
def export_subdomains():
    if not app._db_loaded():
        return jsonify([])
    domain = request.args.get('domain', '').strip().lower()
    if not domain:
        return jsonify([])
    rows = subdomain_utils.list_subdomains(domain)
    fmt = request.args.get('format', 'json')
    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['subdomain', 'domain', 'source', 'cdx_indexed'])
        for r in rows:
            writer.writerow([r['subdomain'], r['domain'], r['source'], r['cdx_indexed']])
        return Response(output.getvalue(), mimetype='text/csv')
    if fmt == 'md':
        lines = ['| subdomain | domain | source | cdx_indexed |', '|---|---|---|---|']
        for r in rows:
            lines.append(f"| {r['subdomain']} | {r['domain']} | {r['source']} | {int(r['cdx_indexed'])} |")
        return Response('\n'.join(lines), mimetype='text/markdown')
    return jsonify(rows)


@bp.route('/mark_subdomain_cdx', methods=['POST'])
def mark_subdomain_cdx():
    if not app._db_loaded():
        return ('', 400)
    subdomain = request.form.get('subdomain', '').strip().lower()
    if not subdomain:
        return ('', 400)
    subdomain_utils.mark_cdxed(subdomain)
    return ('', 204)


@bp.route('/scrape_subdomains', methods=['POST'])
def scrape_subdomains():
    """Scrape existing URL records and insert any discovered subdomains."""
    if not app._db_loaded():
        return ('', 400)
    domain = request.form.get('domain', '').strip().lower()
    if domain and not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
        return ('Invalid domain', 400)
    inserted = subdomain_utils.scrape_from_urls(domain or None)
    return jsonify({'inserted': inserted})
