import json
import re
from pathlib import Path

REPORT_PATH = Path('reports/report.json')
CSS_PATH = Path('static/base.css')
PREFIX = '.retrorecon-root '

# Load report.json
report = json.loads(REPORT_PATH.read_text())
selectors = report['unscoped_selectors'].get(str(CSS_PATH), [])

if not selectors:
    print('No unscoped selectors found in report.json for', CSS_PATH)
    exit()

css_text = CSS_PATH.read_text()

for sel in selectors:
    # Escape special chars for regex
    escaped = re.escape(sel)
    pattern = r'(^|\n)(' + escaped + r')\s*{'
    repl = lambda m: f"{m.group(1)}{PREFIX}{sel} {{"
    css_text = re.sub(pattern, repl, css_text)

CSS_PATH.write_text(css_text)
print('Prefixed', len(selectors), 'selectors in', CSS_PATH)
