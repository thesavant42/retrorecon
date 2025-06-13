import os, json
from bs4 import BeautifulSoup

coverage = {
    'button': {'total': 0, 'styled': 0},
    'input': {'total': 0, 'styled': 0},
    'select': {'total': 0, 'styled': 0},
    'checkbox': {'total': 0, 'styled': 0},
}

styled_classes = {
    'button': {'btn', 'dropbtn', 'explode-btn', 'bulk-action-btn', 'delete-btn', 'copy-btn', 'disabled-btn'},
    'input': {'form-input', 'form-file', 'bulk-tag-input'},
    'select': {'form-select'},
    'checkbox': {'form-checkbox', 'row-checkbox'},
}

def audit_html(path: str) -> None:
    """Update ``coverage`` counts based on the HTML file at ``path``."""

    with open(path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    for b in soup.find_all('button'):
        coverage['button']['total'] += 1
        if set(b.get('class', [])) & styled_classes['button']:
            coverage['button']['styled'] += 1
    for inp in soup.find_all('input'):
        typ = inp.get('type', 'text')
        if typ == 'hidden':
            continue
        coverage['input']['total'] += 1
        classes = set(inp.get('class', []))
        if typ == 'checkbox':
            coverage['checkbox']['total'] += 1
            if classes & styled_classes['checkbox']:
                coverage['checkbox']['styled'] += 1
        if classes & styled_classes['input']:
            coverage['input']['styled'] += 1
    for sel in soup.find_all('select'):
        coverage['select']['total'] += 1
        if set(sel.get('class', [])) & styled_classes['select']:
            coverage['select']['styled'] += 1

def audit_css(path: str) -> list[str]:
    """Return selectors in ``path`` that are not scoped under ``.retrorecon-root``."""

    conflicts: list[str] = []
    with open(path, 'r', encoding='utf-8') as f:
        css = f.read()
    for line in css.splitlines():
        line = line.strip()
        if not line or line.startswith('@'):
            continue
        if '{' in line:
            selector = line.split('{')[0].strip()
            if selector.startswith(':root') or selector.startswith('body'):
                continue
            if not selector.startswith('.retrorecon-root'):
                conflicts.append(selector)
    return conflicts

for root, _, files in os.walk('templates'):
    for f in files:
        if f.endswith('.html'):
            audit_html(os.path.join(root, f))

unscoped = {}
for root, _, files in os.walk('static'):
    for f in files:
        if f.endswith('.css'):
            path = os.path.join(root, f)
            c = audit_css(path)
            if c:
                unscoped[path] = c

report = {'coverage': coverage, 'unscoped_selectors': unscoped}
print(json.dumps(report, indent=2))
