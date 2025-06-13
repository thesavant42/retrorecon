import os
import cssutils
from bs4 import BeautifulSoup

# Silence cssutils warnings for cleaner output
cssutils.log.setLevel('FATAL')

# Collect :root variables from CSS

def parse_root_vars(path):
    vars = {}
    sheet = cssutils.parseFile(path)
    for rule in sheet:
        if rule.type == rule.STYLE_RULE and rule.selectorText.strip() == ':root':
            for prop in rule.style:
                if prop.name.startswith('--'):
                    vars[prop.name] = prop.value
    return vars

# Collect selectors with color-related properties

def collect_color_rules(path):
    results = []
    sheet = cssutils.parseFile(path)
    for rule in sheet:
        if rule.type == rule.STYLE_RULE:
            colors = {}
            for prop in rule.style:
                if prop.name in ('color', 'background', 'background-color'):
                    colors[prop.name] = prop.value
            if colors:
                results.append({'file': path, 'selector': rule.selectorText, 'props': colors})
    return results

# Parse HTML to gather used tags

def collect_tags(directory='templates'):
    tags = {}
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith('.html'):
                with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                    soup = BeautifulSoup(fh, 'html.parser')
                for el in soup.find_all(True):
                    tags[el.name] = tags.get(el.name, 0) + 1
    return tags

# Generate HTML report

def main():
    base_vars = parse_root_vars(os.path.join('static', 'base.css'))
    theme_vars = {}
    theme_dir = os.path.join('static', 'themes')
    if os.path.isdir(theme_dir):
        for f in sorted(os.listdir(theme_dir)):
            if f.endswith('.css'):
                theme_vars[f] = parse_root_vars(os.path.join(theme_dir, f))

    color_rules = []
    for root, _, files in os.walk('static'):
        for f in files:
            if f.endswith('.css'):
                color_rules.extend(collect_color_rules(os.path.join(root, f)))

    tags = collect_tags()

    html = ["<html><head><meta charset='utf-8'>",
            "<title>Style Report</title>",
            "<style>table{border-collapse:collapse;}td,th{border:1px solid #ccc;padding:4px;} .swatch{width:40px;height:20px;display:inline-block;border:1px solid #000;}</style>",
            "</head><body>"]

    html.append("<h1>Base Variables</h1><table><tr><th>Variable</th><th>Value</th><th>Swatch</th></tr>")
    for k,v in base_vars.items():
        html.append(f"<tr><td>{k}</td><td>{v}</td><td><span class='swatch' style='background:{v}'></span></td></tr>")
    html.append("</table>")

    html.append("<h1>Theme Variables</h1>")
    for theme, vars in theme_vars.items():
        html.append(f"<h2>{theme}</h2><table><tr><th>Variable</th><th>Value</th><th>Swatch</th></tr>")
        for k,v in vars.items():
            html.append(f"<tr><td>{k}</td><td>{v}</td><td><span class='swatch' style='background:{v}'></span></td></tr>")
        html.append("</table>")

    html.append("<h1>Used HTML Tags</h1><table><tr><th>Tag</th><th>Count</th></tr>")
    for tag,count in sorted(tags.items()):
        html.append(f"<tr><td>{tag}</td><td>{count}</td></tr>")
    html.append("</table>")

    html.append("<h1>Color Rules</h1><table><tr><th>File</th><th>Selector</th><th>Property</th><th>Value</th><th>Swatch</th></tr>")
    for rule in color_rules:
        for prop,val in rule['props'].items():
            html.append(f"<tr><td>{rule['file']}</td><td>{rule['selector']}</td><td>{prop}</td><td>{val}</td><td><span class='swatch' style='{prop}:{val}'></span></td></tr>")
    html.append("</table>")

    html.append("</body></html>")

    with open('reports/style_report.html', 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))

if __name__ == '__main__':
    main()
