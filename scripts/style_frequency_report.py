import os
import re
from collections import defaultdict
from typing import Dict, List

import cssutils

cssutils.log.setLevel('FATAL')

COLOR_PROPS = {
    'color', 'background', 'background-color', 'border', 'border-color',
    'border-top-color', 'border-right-color', 'border-bottom-color',
    'border-left-color', 'outline-color', 'text-decoration-color',
    'fill', 'stroke', 'box-shadow', 'text-shadow'
}
FONT_PROPS = {'font-family'}
SIZE_PROPS = {'font-size'}
TEXT_EFFECT_PROPS = {
    'font-style', 'font-weight', 'text-decoration', 'text-transform',
    'text-shadow', 'letter-spacing', 'text-align'
}

HEX_RE = re.compile(r'#([0-9a-fA-F]{3,6})')
RGB_RE = re.compile(r'rgba?\(([^)]+)\)')
NAME_MAP = {
    'black': '#000000',
    'white': '#ffffff',
}

def normalize_color(token: str) -> str:
    token = token.strip().lower()
    if token in NAME_MAP:
        return NAME_MAP[token]
    m = HEX_RE.fullmatch(token)
    if m:
        hexval = m.group(1)
        if len(hexval) == 3:
            hexval = ''.join(c*2 for c in hexval)
        return f'#{hexval.lower()}'
    m = RGB_RE.fullmatch(token)
    if m:
        parts = [p.strip() for p in m.group(1).split(',')]
        if len(parts) >= 3:
            try:
                r = int(round(float(parts[0])))
                g = int(round(float(parts[1])))
                b = int(round(float(parts[2])))
                return f'#{r:02x}{g:02x}{b:02x}'
            except ValueError:
                pass
    return token

def collect_css_files() -> List[str]:
    files: List[str] = []
    for root, _, fs in os.walk('static'):
        for f in fs:
            if f.endswith('.css'):
                files.append(os.path.join(root, f))
    return files

def analyze() -> Dict[str, Dict[str, int]]:
    colors: Dict[str, int] = defaultdict(int)
    fonts: Dict[str, int] = defaultdict(int)
    sizes: Dict[str, int] = defaultdict(int)
    effects: Dict[str, int] = defaultdict(int)

    token_re = re.compile(
        r'#(?:[0-9a-fA-F]{3,8})'
        r'|rgba?\([^)]*\)'
        r'|hsla?\([^)]*\)'
        r'|\b(?:transparent|currentcolor|black|white|red|green|blue|orange|purple|yellow|grey|gray|cyan|magenta)\b',
        re.I,
    )

    for path in collect_css_files():
        sheet = cssutils.parseFile(path)
        for rule in sheet:
            if rule.type != rule.STYLE_RULE:
                continue
            for prop in rule.style:
                name = prop.name
                value = prop.value
                if name in COLOR_PROPS:
                    for tok in token_re.findall(value):
                        norm = normalize_color(tok)
                        colors[norm] += 1
                elif name in FONT_PROPS:
                    fonts[value.strip()] += 1
                elif name in SIZE_PROPS:
                    sizes[value.strip()] += 1
                elif name in TEXT_EFFECT_PROPS:
                    effects[f'{name}:{value.strip()}'] += 1
    return {
        'colors': colors,
        'fonts': fonts,
        'sizes': sizes,
        'effects': effects,
    }


def render_table(title: str, data: Dict[str, int], sample_style: str) -> str:
    rows = [f"<h2>{title}</h2>", "<table><tr><th>Value</th><th>Count</th><th>Sample</th></tr>"]
    for val, count in sorted(data.items(), key=lambda x: x[1], reverse=True):
        style = sample_style.format(val)
        rows.append(f"<tr><td>{val}</td><td>{count}</td><td><span style='{style}'>Sample</span></td></tr>")
    rows.append("</table>")
    return '\n'.join(rows)


def main() -> None:
    stats = analyze()
    html = ["<html><head><meta charset='utf-8'>",
            "<title>Style Frequency Report</title>",
            "<style>table{border-collapse:collapse;margin-bottom:1em;}td,th{border:1px solid #ccc;padding:4px;}</style>",
            "</head><body>",
            "<h1>Style Frequency Report</h1>"]
    html.append(render_table('Colors', stats['colors'], 'color:{0};'))
    html.append(render_table('Fonts', stats['fonts'], 'font-family:{0};'))
    html.append(render_table('Font Sizes', stats['sizes'], 'font-size:{0};'))
    html.append(render_table('Text Effects', stats['effects'], '{0}'))
    html.append("</body></html>")
    os.makedirs('reports', exist_ok=True)
    with open('reports/style_frequency.html', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))

if __name__ == '__main__':
    main()
