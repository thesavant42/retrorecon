import os
from typing import Dict, List, Tuple


def _parse_theme_colors(themes_dir: str, filename: str) -> Tuple[str, str]:
    """Return ``(bg, fg)`` colors parsed from the given theme file."""
    bg = '#000000'
    fg = '#ffffff'
    try:
        with open(os.path.join(themes_dir, filename)) as fh:
            for line in fh:
                if '--bg-color' in line:
                    bg = line.split(':')[1].strip().rstrip(';')
                elif '--fg-color' in line:
                    fg = line.split(':')[1].strip().rstrip(';')
                if 'font-family' in line:
                    break
    except OSError:
        pass
    return bg, fg


def load_theme_data(root_path: str) -> Tuple[str, List[str], Dict[str, Tuple[str, str]], str, List[str]]:
    """Return theme related paths and info for the given ``root_path``."""
    themes_dir = os.path.join(root_path, 'static', 'themes')
    if os.path.isdir(themes_dir):
        available_themes = sorted([f for f in os.listdir(themes_dir) if f.endswith('.css')])
    else:
        available_themes = []
    theme_swatches = {t: _parse_theme_colors(themes_dir, t) for t in available_themes}

    backgrounds_dir = os.path.join(root_path, 'static', 'img')
    if os.path.isdir(backgrounds_dir):
        available_backgrounds = sorted([
            f for f in os.listdir(backgrounds_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])
    else:
        available_backgrounds = []

    return themes_dir, available_themes, theme_swatches, backgrounds_dir, available_backgrounds

