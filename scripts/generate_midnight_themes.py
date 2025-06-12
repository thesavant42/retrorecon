"""Generate Midnight City theme CSS files.

This script reads ``dark_combos.html`` for the list of dark color combinations
used by the project and writes a ``theme-XXX.css`` file for each combo.  The
generated styles scope everything under the ``.retrorecon-root`` container and
apply consistent colors to all button and input types.

Yellow text colors are skipped to keep the palette pleasant in dark mode.
"""

from __future__ import annotations

import os
import re
from typing import Iterable, Tuple


THEME_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "themes")
TABLE_FILE = os.path.join(THEME_DIR, "midnight_city_combos.md")
COMBO_HTML = os.path.join(THEME_DIR, "dark_combos.html")


ROW_RE = re.compile(r"<tr><td>(\d+)</td><td>(#[0-9a-fA-F]{6})</td><td>(#[0-9a-fA-F]{6})")


def parse_combos() -> Iterable[Tuple[str, str, str]]:
    """Return (code, background, foreground) tuples from ``dark_combos.html``."""

    with open(COMBO_HTML, "r", encoding="utf-8") as fh:
        for line in fh:
            m = ROW_RE.search(line)
            if m:
                code, bg, fg = m.groups()
                yield code, bg.lower(), fg.lower()


def is_yellowish(hex_color: str) -> bool:
    """Heuristic check for yellow hues."""

    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return r > 200 and g > 200 and max(r, g) - b > 30


CSS_TEMPLATE = """/* Midnight City combo */
:root {{
  --bg-color: {bg};
  --fg-color: {fg};
}}

.retrorecon-root {{
  background: var(--bg-color);
  color: var(--fg-color);
  font-family: system-ui, sans-serif;
}}

body.bg-hidden {{ background-image: none !important; }}

/* Apply colors to all control types */
.retrorecon-root button,
.retrorecon-root input[type="button"],
.retrorecon-root input[type="submit"],
.retrorecon-root input[type="reset"] {{
  background: var(--fg-color);
  color: var(--bg-color);
  border: 1px solid var(--fg-color);
}}

.retrorecon-root input:not([type="button"]):not([type="submit"]):not([type="reset"]),
.retrorecon-root select,
.retrorecon-root textarea {{
  background: var(--bg-color);
  color: var(--fg-color);
  border: 1px solid var(--fg-color);
}}

.retrorecon-root .form-checkbox {{
  accent-color: var(--fg-color);
}}
"""


def main() -> None:
    combos = [(c, bg, fg) for c, bg, fg in parse_combos() if not is_yellowish(fg)]

    os.makedirs(THEME_DIR, exist_ok=True)
    rows = []
    for code, bg, fg in combos:
        rows.append((code, bg, fg))
        css = CSS_TEMPLATE.format(bg=bg, fg=fg)
        with open(os.path.join(THEME_DIR, f"theme-{code}.css"), "w", encoding="utf-8") as cf:
            cf.write(css)

    with open(TABLE_FILE, "w", encoding="utf-8") as f:
        f.write("| Code | Background | Text |\n")
        f.write("|------|------------|------|\n")
        for code, bg, fg in rows:
            f.write(f"| {code} | {bg} | {fg} |\n")


if __name__ == "__main__":
    main()

