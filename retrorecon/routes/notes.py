import app
from flask import Blueprint, request, jsonify
from retrorecon.services import (
    load_saved_tags,
    save_saved_tags,
    get_notes,
    add_note,
    update_note,
    delete_note_entry,
    delete_all_notes,
    export_notes_data,
)

bp = Blueprint('notes', __name__)

@bp.route('/saved_tags', methods=['GET', 'POST'])
def saved_tags_route():
    if request.method == 'GET':
        return jsonify({'tags': load_saved_tags(app.SAVED_TAGS_FILE)})
    tag = request.form.get('tag', '').strip()
    if not tag:
        return ('', 400)
    if not tag.startswith('#'):
        tag = '#' + tag
    tags = load_saved_tags(app.SAVED_TAGS_FILE)
    if tag not in tags:
        tags.append(tag)
        save_saved_tags(app.SAVED_TAGS_FILE, tags)
    return ('', 204)

@bp.route('/delete_saved_tag', methods=['POST'])
def delete_saved_tag():
    tag = request.form.get('tag', '').strip()
    if not tag:
        return ('', 400)
    if not tag.startswith('#'):
        tag = '#' + tag
    tags = load_saved_tags(app.SAVED_TAGS_FILE)
    if tag in tags:
        tags.remove(tag)
        save_saved_tags(app.SAVED_TAGS_FILE, tags)
    return ('', 204)

@bp.route('/notes/<int:url_id>', methods=['GET'])
def notes_get(url_id: int):
    if not app._db_loaded():
        return jsonify([])
    rows = get_notes(url_id)
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
        update_note(note_id, content)
    else:
        add_note(url_id, content)
    return ('', 204)

@bp.route('/delete_note', methods=['POST'])
def delete_note_route():
    note_id = request.form.get('note_id', type=int)
    url_id = request.form.get('url_id', type=int)
    delete_all = request.form.get('all', '0') == '1'
    if note_id:
        delete_note_entry(note_id)
    elif url_id and delete_all:
        delete_all_notes(url_id)
    else:
        return ('', 400)
    return ('', 204)

@bp.route('/export_notes', methods=['GET'])
def export_notes():
    if not app._db_loaded():
        return jsonify([])
    data = export_notes_data()
    return jsonify(data)
