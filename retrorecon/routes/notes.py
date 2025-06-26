import app
from flask import Blueprint, request, jsonify
from retrorecon import saved_tags as saved_tags_mod

bp = Blueprint('notes', __name__)

@bp.route('/saved_tags', methods=['GET', 'POST'])
def saved_tags_route():
    if request.method == 'GET':
        return jsonify({'tags': app.load_saved_tags()})
    tag = request.form.get('tag', '').strip()
    color = request.form.get('color', '').strip() or saved_tags_mod.DEFAULT_COLOR
    if not tag:
        return ('', 400)
    if not tag.startswith('#'):
        tag = '#' + tag
    if not color.startswith('#'):
        color = '#' + color
    tags = app.load_saved_tags()
    names = [t['name'] for t in tags]
    if tag not in names:
        tags.append({'name': tag, 'color': color})
        app.save_saved_tags(tags)
    return ('', 204)

@bp.route('/delete_saved_tag', methods=['POST'])
def delete_saved_tag():
    tag = request.form.get('tag', '').strip()
    if not tag:
        return ('', 400)
    if not tag.startswith('#'):
        tag = '#' + tag
    tags = app.load_saved_tags()
    filtered = [t for t in tags if t['name'] != tag]
    if len(filtered) != len(tags):
        app.save_saved_tags(filtered)
    return ('', 204)

@bp.route('/rename_saved_tag', methods=['POST'])
def rename_saved_tag():
    old_tag = request.form.get('old_tag', '').strip()
    new_tag = request.form.get('new_tag', '').strip()
    color = request.form.get('color', '').strip()
    if not old_tag or not new_tag:
        return ('', 400)
    if not old_tag.startswith('#'):
        old_tag = '#' + old_tag
    if not new_tag.startswith('#'):
        new_tag = '#' + new_tag
    if color and not color.startswith('#'):
        color = '#' + color
    tags = app.load_saved_tags()
    updated = False
    for t in tags:
        if t['name'] == old_tag:
            t['name'] = new_tag
            if color:
                t['color'] = color
            updated = True
    if updated:
        names = [t['name'] for t in tags]
        if len(set(names)) != len(names):
            tags = [dict(name=n, color=c) for n,c in {(t['name'], t['color']) for t in tags}]
        app.save_saved_tags(tags)
    return ('', 204)

@bp.route('/notes/<int:url_id>', methods=['GET'])
def notes_get(url_id: int):
    if not app._db_loaded():
        return jsonify([])
    rows = app.get_notes(url_id)
    return jsonify([
        {
            'id': r['id'],
            'url_id': r['url_id'],
            'content': r['content'],
            'created_at': r['created_at'],
            'updated_at': r['updated_at'],
        }
        for r in rows
    ])

@bp.route('/notes', methods=['POST'])
def notes_post():
    if not app._db_loaded():
        return ('', 400)
    url_id = request.form.get('url_id', type=int)
    content = request.form.get('content', '').strip()
    if not url_id or not content:
        return ('', 400)
    note_id = request.form.get('note_id', type=int)
    if note_id:
        app.update_note(note_id, content)
    else:
        app.add_note(url_id, content)
    return ('', 204)

@bp.route('/delete_note', methods=['POST'])
def delete_note_route():
    note_id = request.form.get('note_id', type=int)
    url_id = request.form.get('url_id', type=int)
    delete_all = request.form.get('all', '0') == '1'
    if note_id:
        app.delete_note_entry(note_id)
    elif url_id and delete_all:
        app.delete_all_notes(url_id)
    else:
        return ('', 400)
    return ('', 204)

@bp.route('/export_notes', methods=['GET'])
def export_notes():
    if not app._db_loaded():
        return jsonify([])
    data = app.export_notes_data()
    return jsonify(data)


@bp.route('/text_notes', methods=['GET', 'POST'])
def text_notes_route():
    if request.method == 'GET':
        if not app._db_loaded():
            return jsonify([])
        rows = app.get_text_notes()
        return jsonify([
            {
                'id': r['id'],
                'content': r['content'],
                'created_at': r['created_at'],
                'updated_at': r['updated_at'],
            }
            for r in rows
        ])
    if not app._db_loaded():
        return ('', 400)
    content = request.form.get('content', '').strip()
    if not content:
        return ('', 400)
    note_id = request.form.get('note_id', type=int)
    if note_id:
        app.update_text_note(note_id, content)
    else:
        app.add_text_note(content)
    return ('', 204)


@bp.route('/delete_text_note', methods=['POST'])
def delete_text_note():
    note_id = request.form.get('note_id', type=int)
    if not note_id:
        return ('', 400)
    app.delete_text_note_entry(note_id)
    return ('', 204)
