import json
from collections import defaultdict
from pathlib import Path

REPORT_PATH = Path('reports/report.json')
report = json.loads(REPORT_PATH.read_text())

files = report.get('unscoped_selectors', {})
selector_map = defaultdict(list)

for path, selectors in files.items():
    for sel in selectors:
        selector_map[sel].append(path)

conflicts = {sel: paths for sel, paths in selector_map.items() if len(paths) > 1}

if conflicts:
    print(json.dumps(conflicts, indent=2))
else:
    print("No conflicting selectors found.")
