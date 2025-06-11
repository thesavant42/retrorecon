import os
import plistlib
import random
import string
import urllib.request

XML_URL = "https://raw.githubusercontent.com/Chirag-Khandelwal/iterm2-midnight-city/refs/heads/master/midnight-city.itermcolors"
THEME_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'themes')
TABLE_FILE = os.path.join(THEME_DIR, 'midnight_city_combos.md')


def fetch_colors():
    with urllib.request.urlopen(XML_URL) as f:
        data = plistlib.loads(f.read())
    return [v for k, v in data.items() if 'Color' in k]


def to_hex(c):
    r = int(c['Red Component'] * 255)
    g = int(c['Green Component'] * 255)
    b = int(c['Blue Component'] * 255)
    return f"#{r:02x}{g:02x}{b:02x}"


def random_code(length=4):
    return ''.join(random.choices(string.ascii_lowercase, k=length))


def main():
    colors = [to_hex(c) for c in fetch_colors()]
    combos = []
    for i in range(len(colors)):
        for j in range(i + 1, len(colors)):
            combos.append((colors[i], colors[j]))
    random.seed(42)
    os.makedirs(THEME_DIR, exist_ok=True)
    rows = []
    for bg, fg in combos:
        code = random_code()
        rows.append((code, bg, fg))
        css = f"/* Midnight City combo */\nbody {{\n  background: {bg};\n  color: {fg};\n  font-family: system-ui, sans-serif;\n}}\nbody.bg-hidden {{ background-image: none !important; }}\n"
        with open(os.path.join(THEME_DIR, f"theme-{code}.css"), 'w') as cf:
            cf.write(css)
    with open(TABLE_FILE, 'w') as f:
        f.write('| Code | Background | Text |\n')
        f.write('|------|------------|------|\n')
        for code, bg, fg in rows:
            f.write(f'| {code} | {bg} | {fg} |\n')

if __name__ == '__main__':
    main()
