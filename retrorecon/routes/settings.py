import os
import re
import app
from flask import Blueprint, request, redirect, url_for, flash, session

bp = Blueprint('settings', __name__)

@bp.route('/set_theme', methods=['POST'])
def set_theme():
    theme = request.form.get('theme', '')
    if theme in app.AVAILABLE_THEMES:
        session['theme'] = theme
        flash(f"Theme changed to '{theme.replace('theme-', '').replace('.css', '').capitalize()}'", "success")
    else:
        flash("Invalid theme selection.", "error")
    return redirect(url_for('index'))


@bp.route('/set_background', methods=['POST'])
def set_background():
    bg = request.form.get('background', '')
    if bg in app.AVAILABLE_BACKGROUNDS:
        session['background'] = bg
        return ('', 204)
    return ('Invalid background', 400)


@bp.route('/set_panel_opacity', methods=['POST'])
def set_panel_opacity():
    try:
        opacity = float(request.form.get('opacity', '1'))
    except ValueError:
        return ('Invalid value', 400)
    opacity = max(0.1, min(opacity, 1.0))
    session['panel_opacity'] = opacity
    return ('', 204)


@bp.route('/set_font_size', methods=['POST'])
def set_font_size():
    try:
        size = int(request.form.get('size', '14'))
    except ValueError:
        return ('Invalid value', 400)
    size = max(10, min(size, 18))
    theme = request.form.get('theme') or session.get('theme')
    if not theme and app.AVAILABLE_THEMES:
        theme = app.AVAILABLE_THEMES[0]
    if not theme or theme not in app.AVAILABLE_THEMES:
        return ('Invalid theme', 400)
    path = os.path.join(app.THEMES_DIR, theme)
    try:
        lines = open(path).read().splitlines()
    except OSError:
        return ('Theme not found', 404)
    new_lines = []
    in_pagination = False
    in_footer = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('.retrorecon-root .pagination'):
            in_pagination = True
        elif stripped.startswith('.retrorecon-root .footer'):
            in_footer = True
        if 'font-size:' in line:
            if '13.333px' in line:
                line = re.sub(r'font-size:\s*[^;]+;', f'font-size: {size}px;', line)
            elif in_pagination or in_footer:
                line = re.sub(r'font-size:\s*[^;]+;', f'font-size: {size}px;', line)
        if in_pagination and '}' in line:
            in_pagination = False
        if in_footer and '}' in line:
            in_footer = False
        new_lines.append(line)
    with open(path, 'w') as fh:
        fh.write('\n'.join(new_lines) + '\n')
    return ('', 204)


@bp.route('/set_items_per_page', methods=['POST'])
def set_items_per_page():
    try:
        count = int(request.form.get('count', ''))
    except ValueError:
        return ('Invalid value', 400)
    if count not in app.ITEMS_PER_PAGE_OPTIONS:
        return ('Invalid value', 400)
    session['items_per_page'] = count
    return redirect(url_for('urls.index'))
