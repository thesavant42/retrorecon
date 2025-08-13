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
    if fmt == 'html':
        html_lines = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '<title>Exported URLs</title>',
            '<style>',
            'body { font-family: monospace; margin: 20px; background: #000; color: #fff; }',
            'table { border-collapse: collapse; width: 100%; }',
            'th, td { border: 1px solid #444; padding: 8px; text-align: left; }',
            'th { background: #222; }',
            'a { color: #0af; text-decoration: none; }',
            'a:hover { text-decoration: underline; }',
            '.timestamp { font-size: 0.9em; color: #aaa; }',
            '.status { text-align: center; font-weight: bold; }',
            '.status-2 { color: #0a0; }',
            '.status-3 { color: #fa0; }',
            '.status-4 { color: #f50; }',
            '.status-5 { color: #f00; }',
            '.tags { font-size: 0.8em; color: #aaf; }',
            '</style>',
            '</head>',
            '<body>',
            f'<h1>Exported URLs ({len(rows)} records)</h1>',
            '<table>',
            '<thead>',
            '<tr>',
            '<th>URL</th>',
            '<th>Timestamp</th>',
            '<th>Status</th>',
            '<th>MIME Type</th>',
            '<th>Tags</th>',
            '</tr>',
            '</thead>',
            '<tbody>'
        ]
        
        for r in rows:
            url = r['url'] or ''
            timestamp = r['timestamp'] or ''
            status = r['status_code'] or ''
            mime = r['mime_type'] or ''
            tags = r['tags'] or ''
            
            # Create hyperlinked URL
            url_cell = f'<a href="{url}" target="_blank" rel="noopener">{url}</a>' if url else ''
            
            # Style status code
            status_class = f'status-{str(status)[0]}' if status and str(status)[0].isdigit() else 'status'
            status_cell = f'<span class="status {status_class}">{status}</span>' if status else ''
            
            # Format timestamp
            timestamp_cell = f'<span class="timestamp">{timestamp}</span>' if timestamp else ''
            
            # Format tags
            tags_cell = f'<span class="tags">{tags}</span>' if tags else ''
            
            html_lines.append(
                f'<tr>'
                f'<td>{url_cell}</td>'
                f'<td>{timestamp_cell}</td>'
                f'<td>{status_cell}</td>'
                f'<td>{mime}</td>'
                f'<td>{tags_cell}</td>'
                f'</tr>'
            )
        
        html_lines.extend([
            '</tbody>',
            '</table>',
            '</body>',
            '</html>'
        ])
        
        return Response('\n'.join(html_lines), mimetype='text/html')
    return jsonify(rows)
