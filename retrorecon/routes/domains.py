import io
import csv
import re
import json
from flask import Blueprint, request, jsonify, Response, current_app, render_template_string
from .dynamic import dynamic_template, render_from_payload, schema_registry, html_generator
import app
from retrorecon import subdomain_utils, status as status_mod
from retrorecon import domain_sort
from collections import defaultdict
import tldextract

# Use a bundled suffix list and disable caching to avoid network requests
# and file lock contention when extracting domains.
_EXTRACTOR = tldextract.TLDExtract(cache_dir=False, suffix_list_urls=())

bp = Blueprint('domains', __name__)


def _extract_root(domain: str) -> str:
    """Return the registered domain using a local suffix cache."""
    ext = _EXTRACTOR(domain)
    if ext.domain and ext.suffix:
        return f"{ext.domain}.{ext.suffix}"
    return domain


def _build_tree(domains):
    tree = {}
    for dom in sorted(domains, key=lambda d: (len(d.split('.')), d)):
        tree.setdefault(dom, [])
    for dom in tree:
        for other in tree:
            if other == dom:
                continue
            if other.endswith('.' + dom):
                tree[dom].append(other)
    return tree


def _render_tree_md(tree, root, domains, level=0, printed=None):
    """Return a Markdown bullet list of the domain tree."""
    if printed is None:
        printed = set()
    if root in printed:
        return ""
    indent = '  ' * level
    line = f"{indent}- {root}\n"
    printed.add(root)
    children = [d for d in domains if d.endswith('.' + root) and d not in printed]
    children = sorted(children, key=lambda d: (len(d.split('.')), d))
    for child in children:
        line += _render_tree_md(tree, child, domains, level + 1, printed)
    return line


def _render_tree_html(tree, root, domains, printed=None):
    """Return nested <li> elements wrapped in <details> for collapsible tree."""
    if printed is None:
        printed = set()
    if root in printed:
        return ""
    printed.add(root)
    children = [d for d in domains if d.endswith('.' + root) and d not in printed]
    children = sorted(children, key=lambda d: (len(d.split('.')), d))
    count = subdomain_utils.count_urls_for_host(root)
    label = f"{root} ({count})" if count else root
    if children:
        line = f'<li><details class="collapsible" open><summary>{label}</summary><ul>'
        for child in children:
            line += _render_tree_html(tree, child, domains, printed)
        line += '</ul></details></li>'
    else:
        line = f'<li>{label}</li>'
    return line


def _render_domain_sort_output(roots: dict) -> str:
    """Return the full HTML output for the domain sort table and tree."""
    rows = []
    for root in sorted(roots):
        url_count = subdomain_utils.count_urls_for_root(root)
        rows.append(
            "<tr>"
            f"<td><a href='#' class='domain-sort-toggle' data-target='root-{root}'>"
            f"{root}</a></td>"
            f"<td>{len(roots[root])}</td>"
            f"<td>{url_count}</td>"
            "</tr>"
        )
    table = (
        "<table class='domain-sort-summary'><thead><tr><th>Domain</th><th>Subdomains</th><th>URLs</th></tr></thead>"
        "<tbody>" + ''.join(rows) + "</tbody></table>"
    )
    total_hosts = len({h for v in roots.values() for h in v})
    counts = f"<p class='domain-sort-counts'>{total_hosts} hosts across {len(roots)} root domains</p>"
    output = counts + table
    for root in sorted(roots):
        tree = _build_tree(roots[root])
        top_level = [
            d
            for d in roots[root]
            if d == root or (d.endswith('.' + root) and d.count('.') == root.count('.') + 1)
        ]
        items = ''.join(
            _render_tree_html(tree, dom, roots[root])
            for dom in sorted(top_level, key=lambda d: (len(d.split('.')), d))
        )
        output += (
            f"<details class='collapsible domain-sort-root' open id='root-{root}'>"
            f"<summary>{root}</summary><ul class='domain-sort-tree'>{items}</ul></details>"
        )
    return output


def _summary_data() -> dict:
    """Return aggregate subdomain summary information."""
    if not app._db_loaded():
        return {
            'total_domains': 0,
            'total_hosts': 0,
            'top_subdomains': [],
            'lonely_subdomains': [],
        }

    rows = subdomain_utils.list_all_subdomains()
    hosts = [r['subdomain'] for r in rows]
    roots = {r['domain'] for r in rows}
    for host in subdomain_utils.list_url_hosts():
        if host not in hosts:
            hosts.append(host)
        roots.add(_extract_root(host))
    tree = domain_sort.aggregate_hosts(hosts)
    flat = domain_sort.flatten_tree(tree)
    flat_sorted = sorted(flat, key=lambda x: x[1], reverse=True)
    top_subs = flat_sorted[:5]
    lonely_subs = sorted(flat, key=lambda x: x[1])[:5]
    return {
        'total_domains': len(roots),
        'total_hosts': len(set(hosts)),
        'top_subdomains': top_subs,
        'lonely_subdomains': lonely_subs,
    }



@bp.route('/subdomains', methods=['GET', 'POST'])
def subdomains_route():
    if not app._db_loaded():
        return jsonify({'error': 'no_db'}), 400

    if request.method == 'GET':
        domain = request.args.get('domain', '').strip().lower()
        q = request.args.get('q', '').strip().lower()
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
            if q:
                rows = subdomain_utils.search_subdomains(q, domain or None)
                total = len(rows)
                rows = rows[offset:offset + items]
            else:
                total = subdomain_utils.count_subdomains(domain or None)
                rows = subdomain_utils.list_subdomains_page(domain or None, offset, items)
            total_pages = max(1, (total + items - 1) // items)
            return jsonify({
                'page': page,
                'total_pages': total_pages,
                'total_count': total,
                'results': rows,
            })
        if q:
            return jsonify(subdomain_utils.search_subdomains(q, domain or None))
        if domain:
            return jsonify(subdomain_utils.list_subdomains(domain))
        return jsonify(subdomain_utils.list_all_subdomains())

    domain = request.form.get('domain', '').strip().lower()
    source = request.form.get('source', 'crtsh')
    api_key = request.form.get('api_key', '').strip() or current_app.config.get('VIRUSTOTAL_API', '')

    if source == 'local':
        # Allow single-label hostnames or IPs when scraping local URLs. A very
        # loose check avoids rejecting common internal domains like
        # "localhost" while still filtering obvious bad input.
        if domain and not re.match(r'^[A-Za-z0-9.-]+$', domain):
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
    q = request.args.get('q', '').strip().lower()
    if q:
        rows = [
            r for r in rows
            if q in r['subdomain'].lower()
            or q in r['domain'].lower()
            or q in (r['tags'] or '').lower()
        ]
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


@bp.route('/update_subdomain', methods=['POST'])
def update_subdomain_route():
    """Rename a subdomain entry."""
    if not app._db_loaded():
        return ('', 400)
    domain = request.form.get('domain', '').strip().lower()
    subdomain = request.form.get('subdomain', '').strip().lower()
    new_domain = request.form.get('new_domain', '').strip().lower()
    new_subdomain = request.form.get('new_subdomain', '').strip().lower()
    if not domain or not subdomain or not new_domain or not new_subdomain:
        return ('', 400)
    app.update_subdomain(domain, subdomain, new_domain, new_subdomain)
    return ('', 204)


@bp.route('/subdomain_action', methods=['POST'])
def subdomain_action():
    """Bulk modify or delete subdomains."""
    if not app._db_loaded():
        return ('', 400)
    action = request.form.get('action', '')
    tag = request.form.get('tag', '').strip()
    pairs = request.form.getlist('selected')
    select_all_matching = request.form.get('select_all_matching', 'false').lower() == 'true'
    if select_all_matching:
        q = request.form.get('q', '').strip()
        domain = request.form.get('domain', '').strip().lower() or None
        rows = subdomain_utils.search_subdomains(q, domain) if q else (
            subdomain_utils.list_subdomains(domain) if domain else subdomain_utils.list_all_subdomains()
        )
        pairs = [f"{r['domain']}|{r['subdomain']}" for r in rows]
    count = 0
    for pair in pairs:
        if '|' not in pair:
            continue
        root_domain, sub = pair.split('|', 1)
        if action == 'delete':
            app.delete_subdomain(root_domain, sub)
            count += 1
        elif action == 'add_tag' and tag:
            subdomain_utils.add_tag(root_domain, sub, tag)
            count += 1
        elif action == 'remove_tag' and tag:
            subdomain_utils.remove_tag(root_domain, sub, tag)
            count += 1
        elif action == 'clear_tags':
            subdomain_utils.clear_tags(root_domain, sub)
            count += 1
    return jsonify({'updated': count})

@bp.route('/domain_summary', methods=['GET'])
def domain_summary_page():
    """Return a simple summary of subdomain counts."""
    data = _summary_data()
    return dynamic_template('subdomain_summary.html', **data)


@bp.route('/domain_summary.json', methods=['GET'])
def domain_summary_json():
    """Return subdomain summary as JSON."""
    return jsonify(_summary_data())


@bp.route('/domain_sort', methods=['GET', 'POST'])
def domain_sort_page():
    """Return an overlay that sorts domains recursively."""
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            lines = file.read().decode('utf-8', 'replace').splitlines()
        else:
            lines = request.form.get('domains', '').splitlines()
        domains = [l.strip() for l in lines if l.strip()]
        uploaded = defaultdict(list)
        for dom in domains:
            uploaded[_extract_root(dom)].append(dom)
        # Persist imported domains so the subdomain table reflects them
        if app._db_loaded():
            for root, hosts in uploaded.items():
                subdomain_utils.insert_records(root, hosts, 'domain_sort')
                try:
                    subdomain_utils.scrape_from_urls(root)
                except Exception:
                    pass
            # After inserting, rebuild using every subdomain and URL host
            all_roots = defaultdict(set)
            for row in subdomain_utils.list_all_subdomains():
                all_roots[row['domain']].add(row['subdomain'])
            for host in subdomain_utils.list_url_hosts():
                all_roots[_extract_root(host)].add(host)
            roots = {k: sorted(v) for k, v in all_roots.items()}
        else:
            roots = uploaded

        fmt = request.form.get('format', 'html')
        if fmt not in ('html', 'md'):
            fmt = 'html'
        if fmt == 'md':
            lines = []
            for root in sorted(roots):
                lines.append(f"### {root}")
                tree = _build_tree(roots[root])
                top_level = [d for d in roots[root] if d == root or (d.endswith('.'+root) and d.count('.') == root.count('.') + 1)]
                for dom in sorted(top_level, key=lambda d: (len(d.split('.')), d)):
                    lines.append(_render_tree_md(tree, dom, roots[root]))
            return Response('\n'.join(lines), mimetype='text/markdown')

        output = _render_domain_sort_output(roots)
        return Response(output, mimetype='text/html')

    if app._db_loaded():
        rows = subdomain_utils.list_all_subdomains()
        url_hosts = subdomain_utils.list_url_hosts()
        if rows or url_hosts:
            roots = defaultdict(set)
            for r in rows:
                roots[r['domain']].add(r['subdomain'])
            for host in url_hosts:
                roots[_extract_root(host)].add(host)
            sorted_roots = {k: sorted(v) for k, v in roots.items()}
            output = _render_domain_sort_output(sorted_roots)
            return dynamic_template('domain_sort.html', initial_output=output)
    return dynamic_template('domain_sort.html', initial_output="")


@bp.route('/tools/domain_sort', methods=['GET'])
def domain_sort_full_page():
    return app.index()
