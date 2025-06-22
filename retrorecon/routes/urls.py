import io
import csv
from typing import List, Optional

import app
from flask import Blueprint, request, Response, jsonify

bp = Blueprint('urls', __name__)

@bp.route('/export_urls', methods=['GET'])
def export_urls():
    """Export URL records in various formats."""
    if not app._db_loaded():
        return jsonify([])

    fmt = request.args.get('format', 'json').lower()
    q = request.args.get('q', '').strip()
    select_all = request.args.get('select_all_matching', 'false').lower() == 'true'
    ids: Optional[List[int]] = None
    if not select_all:
        ids = [int(i) for i in request.args.getlist('id') if i.isdigit()]
    rows = app.export_url_data(ids=ids, query=q)

    if fmt == 'txt':
        text = '\n'.join(r['url'] for r in rows)
        return Response(text, mimetype='text/plain')
    if fmt == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['url', 'timestamp', 'status_code', 'mime_type', 'tags'])
        for r in rows:
            writer.writerow([r['url'], r['timestamp'], r['status_code'], r['mime_type'], r['tags']])
        return Response(output.getvalue(), mimetype='text/csv')
    if fmt == 'md':
        lines = ['| url | timestamp | status_code | mime_type | tags |', '|---|---|---|---|---|']
        for r in rows:
            lines.append(f"| {r['url']} | {r['timestamp'] or ''} | {r['status_code'] or ''} | {r['mime_type'] or ''} | {r['tags'] or ''} |")
        return Response('\n'.join(lines), mimetype='text/markdown')
    return jsonify(rows)
