import os
from typing import Dict, List
import cssutils

cssutils.log.setLevel('FATAL')

THEME_DIR = os.path.join('static', 'themes')
CSS_FILES: List[str] = []
base_css = os.path.join('static', 'base.css')
if os.path.exists(base_css):
    CSS_FILES.append(base_css)
if os.path.isdir(THEME_DIR):
    for fname in sorted(os.listdir(THEME_DIR)):
        if fname.endswith('.css'):
            CSS_FILES.append(os.path.join(THEME_DIR, fname))

PROPS = ['color', 'background', 'background-color', 'font-size', 'opacity',
         'min-width', 'padding', 'border']

ELEMENTS = {
    'menu dropdown': '.retrorecon-root .dropdown-content',
    'menu button': '.retrorecon-root .dropbtn',
    'app banner': '.retrorecon-root h1',
    'db banner': '.retrorecon-root .db-info',
    'search input': '.retrorecon-root .search-bar input[type="text"]',
    'tag pill': '.retrorecon-root .tag-pill',
    'search buttons': '.retrorecon-root .search-bar button',
    'pagination': '.retrorecon-root .pagination',
    'results table': '.retrorecon-root .url-table',
    'explode buttons': '.retrorecon-root .explode-btn',
    'copy button': '.retrorecon-root .copy-btn',
    'delete button': '.retrorecon-root .delete-btn',
    'tag input': '.retrorecon-root #bulk-tag-input',
    'tag add button': '.retrorecon-root .bulk-action-btn',
    'footer': '.retrorecon-root .footer',
    'dropdown heading': '.retrorecon-root .fw-bold',
    'fetch url input': '.retrorecon-root #domain-input',
    'json import input': '.retrorecon-root .form-file',
    'db import input': '.retrorecon-root .form-file',
    'map url input': '.retrorecon-root #map-url-input',
    'download url input': '.retrorecon-root #download-url-input',
}

def parse_css(files: List[str]) -> Dict[str, Dict[str, str]]:
    rules: Dict[str, Dict[str, str]] = {}
    for path in files:
        sheet = cssutils.parseFile(path)
        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                selectors = [s.strip() for s in rule.selectorText.split(',')]
                for sel in selectors:
                    rules.setdefault(sel, {})
                    for prop in rule.style:
                        rules[sel][prop.name] = prop.value
                        rules[sel]['__source__'] = path
    return rules

STYLES = parse_css(CSS_FILES)

def check_styles() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for name, selector in ELEMENTS.items():
        rule = STYLES.get(selector)
        prop = ''
        val = ''
        src = ''
        if rule:
            for p in PROPS:
                if p in rule:
                    prop = p
                    val = rule[p]
                    break
            if not prop:
                # fall back to the first property found
                for k, v in rule.items():
                    if not k.startswith('__'):
                        prop = k
                        val = v
                        break
            src = rule.get('__source__', '')
        rows.append({'name': name, 'value': prop, 'actual': val, 'source': src})
    return rows

def to_markdown(rows: List[Dict[str, str]]) -> str:
    lines = [
        '| name | value | expected_value | actual_value | which setting is taking priority in the cascade? |',
        '|------|-------|----------------|--------------|-----------------------------------------------|'
    ]
    for r in rows:
        exp = 'any'
        lines.append(f"| {r['name']} | {r['value']} | {exp} | {r['actual']} | {r['source']} |")
    return '\n'.join(lines)

if __name__ == '__main__':
    md = to_markdown(check_styles())
    print(md)
