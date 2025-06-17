import os
import app
from flask import Blueprint, request, redirect, url_for, flash, send_file, session

bp = Blueprint('db', __name__)

@bp.route('/new_db', methods=['POST'])
def new_db():
    name = request.form.get('db_name', '').strip()
    safe = app._sanitize_db_name(name)
    if not safe:
        flash('Invalid database name.', 'error')
        return redirect(url_for('index'))
    app.close_connection(None)
    temp_path = os.path.join(app.app.root_path, app.TEMP_DB_NAME)
    if app.app.config.get('DATABASE') == temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
    try:
        db_name = app.create_new_db(safe)
        session['db_display_name'] = db_name
        flash('New database created.', 'success')
    except ValueError as e:
        flash(str(e), 'error')
    return redirect(url_for('index'))


@bp.route('/load_db', methods=['POST'])
def load_db_route():
    file = request.files.get('db_file')
    if not file:
        flash("No database file uploaded.", "error")
        return redirect(url_for('index'))
    filename = app._sanitize_db_name(file.filename or '')
    if not filename:
        flash('Invalid database file.', 'error')
        return redirect(url_for('index'))
    db_path = os.path.join(app._get_db_dir(), filename)
    app.close_connection(None)
    temp_path = os.path.join(app._get_db_dir(), app.TEMP_DB_NAME)
    if app.app.config.get('DATABASE') == temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
    try:
        file.save(db_path)
        app.app.config['DATABASE'] = db_path
        app.ensure_schema()
        session['db_display_name'] = filename
        flash("Database loaded.", "success")
    except Exception as e:
        flash(f"Error loading database: {e}", "error")
    return redirect(url_for('index'))


@bp.route('/save_db', methods=['GET'])
def save_db():
    if not app._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    name = request.args.get("name", "").strip()
    if name:
        safe_name = app._sanitize_export_name(name)
    else:
        safe_name = os.path.basename(app.app.config["DATABASE"])
    return send_file(
        app.app.config['DATABASE'],
        as_attachment=True,
        download_name=safe_name
    )


@bp.route('/rename_db', methods=['POST'])
def rename_db():
    new_name = request.form.get('new_name', '').strip()
    safe = app._sanitize_db_name(new_name or '')
    if not safe:
        flash('Invalid database name.', 'error')
        return redirect(url_for('index'))
    if not app._db_loaded():
        flash('No database loaded.', 'error')
        return redirect(url_for('index'))
    app.close_connection(None)
    new_path = os.path.join(app._get_db_dir(), safe)
    try:
        os.rename(app.app.config['DATABASE'], new_path)
    except OSError as e:
        flash(f'Error renaming database: {e}', 'error')
        return redirect(url_for('index'))
    app.app.config['DATABASE'] = new_path
    app.ensure_schema()
    session['db_display_name'] = safe
    flash('Database renamed.', 'success')
    return redirect(url_for('index'))


@bp.route('/stored_dbs', methods=['GET'])
def stored_dbs():
    """Return a JSON list of saved database filenames."""
    db_dir = app._get_db_dir()
    try:
        names = [f for f in os.listdir(db_dir) if f.lower().endswith('.db')]
    except OSError:
        names = []
    return app.jsonify(sorted(names))


@bp.route('/load_saved_db', methods=['POST'])
def load_saved_db():
    filename = request.form.get('db_name', '').strip()
    safe = app._sanitize_db_name(filename)
    if not safe:
        flash('Invalid database name.', 'error')
        return redirect(url_for('index'))
    db_path = os.path.join(app._get_db_dir(), safe)
    if not os.path.exists(db_path):
        flash('Database not found.', 'error')
        return redirect(url_for('index'))
    app.close_connection(None)
    temp_path = os.path.join(app._get_db_dir(), app.TEMP_DB_NAME)
    if app.app.config.get('DATABASE') == temp_path and os.path.exists(temp_path):
        os.remove(temp_path)
    try:
        app.app.config['DATABASE'] = db_path
        app.ensure_schema()
        session['db_display_name'] = safe
        flash('Database loaded.', 'success')
    except Exception as e:
        flash(f'Error loading database: {e}', 'error')
    return redirect(url_for('index'))
