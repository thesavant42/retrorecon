import app
from flask import Blueprint, send_from_directory, Response

bp = Blueprint('core', __name__)

@bp.route('/favicon.ico')
def favicon_ico() -> Response:
    """Serve the favicon.ico from the application root."""
    return send_from_directory(app.app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@bp.route('/favicon.svg')
def favicon_svg() -> Response:
    """Serve the favicon.svg from the application root."""
    return send_from_directory(app.app.root_path, 'favicon.svg', mimetype='image/svg+xml')
