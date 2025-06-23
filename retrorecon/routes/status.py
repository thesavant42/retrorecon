import app
from flask import Blueprint, jsonify

bp = Blueprint('status', __name__)

@bp.route('/status', methods=['GET'])
def status_route():
    """Return the most recent status event and clear the queue."""
    evt = app.status_mod.pop_status()
    last = evt
    while True:
        nxt = app.status_mod.pop_status()
        if not nxt:
            break
        last = nxt
    if not last:
        return ('', 204)
    return jsonify({'code': last[0], 'message': last[1]})
