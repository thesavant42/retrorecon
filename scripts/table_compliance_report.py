#!/usr/bin/env python3
"""Generate an HTML report of tables that do not follow the style guide."""
from pathlib import Path
from bs4 import BeautifulSoup, element

TEMPLATE_DIR = Path('templates')
REPORT_DIR = Path('reports')
REPORT_DIR.mkdir(exist_ok=True)

rows = [
    '<html><head><title>Table Compliance Report</title>',
    '<style>table{border-collapse:collapse;}td,th{border:1px solid #ccc;padding:4px;}</style>',
    '</head><body>',
    '<h1>Table Compliance Report</h1>',
    '<table><tr><th>File</th><th>Issue</th><th>Excerpt</th></tr>'
]

non_compliant = 0

for html_file in sorted(TEMPLATE_DIR.glob('*.html')):
    soup = BeautifulSoup(html_file.read_text(), 'html.parser')
    for table in soup.find_all('table'):
        issues = []
        parent = table
        within_root = False
        while isinstance(parent, element.Tag):
            if 'retrorecon-root' in parent.get('class', []):
                within_root = True
                break
            parent = parent.parent
        if not within_root:
            issues.append('not inside .retrorecon-root')
        if table.has_attr('style'):
            issues.append('inline style')
        if issues:
            non_compliant += 1
            excerpt = (str(table)[:60]
                       .replace('<', '&lt;')
                       .replace('>', '&gt;'))
            rows.append(f"<tr><td>{html_file}</td><td>{', '.join(issues)}</td><td><code>{excerpt}...</code></td></tr>")

if non_compliant == 0:
    rows.append("<tr><td colspan='3'>All tables comply with the style guide.</td></tr>")

rows.append('</table></body></html>')

(REPORT_DIR / 'table_compliance.html').write_text('\n'.join(rows), encoding='utf-8')
print(f"Found {non_compliant} non-compliant tables.")
