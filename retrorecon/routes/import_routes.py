import io
import threading
import app
from flask import Blueprint, request, redirect, url_for, flash, jsonify
from retrorecon import app_utils

bp = Blueprint('import', __name__)


def _background_import(file_content: bytes) -> None:
    app_utils._background_import(file_content, app.app.config['DATABASE'], app.IMPORT_PROGRESS_FILE)


@bp.route('/import_file', methods=['POST'])
@bp.route('/import_json', methods=['POST'])
def import_file():
    file = (
        request.files.get('import_file')
        or request.files.get('json_file')
    )
    if not file:
        flash("No file uploaded for import.", "error")
        return redirect(url_for('overview.index'))

    filename = file.filename or ''
    ext = filename.rsplit('.', 1)[-1].lower()

    if ext != 'json':
        flash('Please upload a JSON file.', 'error')
        return redirect(url_for('overview.index'))

    if not app_utils._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('overview.index'))

    app_utils.clear_import_progress(app.IMPORT_PROGRESS_FILE)
    file_content = file.read()
    app_utils.set_import_progress(app.IMPORT_PROGRESS_FILE, 'starting', 'Starting import...', 0, 0)
    thread = threading.Thread(target=_background_import, args=(file_content,))
    thread.start()
    flash('Import started! Progress will be shown below.', 'success')
    return redirect(url_for('overview.index'))


@bp.route('/import_progress', methods=['GET'])
def import_progress():
    prog = app_utils.get_import_progress(app.IMPORT_PROGRESS_FILE)
    if request.args.get('clear') == '1' and prog.get('status') in ('done', 'failed'):
        app_utils.clear_import_progress(app.IMPORT_PROGRESS_FILE)
    return jsonify({
        'status': prog.get('status', 'idle'),
        'progress': prog.get('current', 0),
        'total': prog.get('total', 0),
        'detail': prog.get('message', '')
    })
