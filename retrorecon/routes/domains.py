import io
import csv
import re
from flask import Blueprint, request, jsonify, render_template, Response
import app
from retrorecon import subdomain_utils, status as status_mod

bp = Blueprint('domains', __name__)


@bp.route('/subdomonster', methods=['GET'])
def subdomonster_page():
    data = []
    if app._db_loaded():
        data = subdomain_utils.list_all_subdomains()
    return render_template('subdomonster.html', initial_data=data)


@bp.route('/tools/subdomonster', methods=['GET'])
def subdomonster_full_page():
    return app.index()


@bp.route('/subdomains', methods=['GET', 'POST'])
def subdomains_route():
    if not app._db_loaded():
        return jsonify({'error': 'no_db'}), 400

    if request.method == 'GET':
        domain = request.args.get('domain', '').strip().lower()
        try:
            page = int(request.args.get('page', '0'))
        except ValueError:
            page = 0
        try:
            items = int(request.args.get('items', '0'))
        except ValueError:
            items = 0
        if page > 0 and items > 0:
            offset = (page - 1) * items
            total = subdomain_utils.count_subdomains(domain or None)
            rows = subdomain_utils.list_subdomains_page(domain or None, offset, items)
            total_pages = max(1, (total + items - 1) // items)
            return jsonify({
                'page': page,
                'total_pages': total_pages,
                'total_count': total,
                'results': rows,
            })
        if domain:
            return jsonify(subdomain_utils.list_subdomains(domain))
        return jsonify(subdomain_utils.list_all_subdomains())

    domain = request.form.get('domain', '').strip().lower()
    source = request.form.get('source', 'crtsh')
    api_key = request.form.get('api_key', '').strip()

    if source == 'local':
        if domain and not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
            return ('Invalid domain', 400)
        status_mod.push_status('subdomonster_local_start', domain or 'all')
        inserted = subdomain_utils.scrape_from_urls(domain or None)
        status_mod.push_status('subdomonster_local_done', str(inserted))
        if domain:
            return jsonify(subdomain_utils.list_subdomains(domain))
        return jsonify(subdomain_utils.list_all_subdomains())

    if not domain:
        return ('Missing domain', 400)
    if not re.match(r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$', domain):
        return ('Invalid domain', 400)
    try:
        if source == 'virustotal':
            if not api_key:
                return ('Missing API key', 400)
            subs = subdomain_utils.fetch_from_virustotal(domain, api_key)
        else:
            subs = subdomain_utils.fetch_from_crtsh(domain)
    except Exception as e:  # pragma: no cover - network errors
        return (f'Error fetching: {e}', 500)
    inserted = subdomain_utils.insert_records(domain, subs, source)
    status_mod.push_status('subdomonster_import_done', f"{domain}:{inserted}")
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
    status_mod.push_status('subdomonster_scrape_start', domain or 'all')
    inserted = subdomain_utils.scrape_from_urls(domain or None)
    status_mod.push_status('subdomonster_scrape_done', str(inserted))
    return jsonify({'inserted': inserted})

@bp.route('/delete_subdomain', methods=['POST'])
def delete_subdomain_route():
    if not app._db_loaded():
        return ('', 400)
    domain = request.form.get('domain', '').strip().lower()
    subdomain = request.form.get('subdomain', '').strip().lower()
    if not domain or not subdomain:
        return ('', 400)
    app.delete_subdomain(domain, subdomain)
    return ('', 204)
