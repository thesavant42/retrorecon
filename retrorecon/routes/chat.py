import app
from flask import Blueprint, request, jsonify

from retrorecon.mcp import RetroReconMCPServer, load_config

bp = Blueprint('chat', __name__, url_prefix='/chat')


def _get_server() -> RetroReconMCPServer:
    """Get or create the MCP server instance."""
    server = getattr(app, 'mcp_server', None)
    if server is None:
        server = RetroReconMCPServer(config=load_config())
        app.mcp_server = server
    _ensure_db_path(server)
    return server


def _ensure_db_path(server: RetroReconMCPServer) -> None:
    db_path = app.app.config.get('DATABASE')
    if db_path and server.db_path != db_path:
        server.update_database_path(db_path)


@bp.route('/message', methods=['POST'])
def handle_chat_message():
    """Process a natural language chat message.

    Users type plain English questions in the chat bar. Raw SQL statements are
    not accepted; if provided, they will be rejected with an error message.
    The MCP server is responsible for translating natural language into SQL
    internally once language model support is enabled.
    """
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message content required'})

    server = _get_server()
    try:
        result = server.answer_question(message)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': str(exc)})


@bp.route('/status', methods=['GET'])
def chat_status():
    """Return health information for the MCP server."""
    try:
        server = _get_server()
    except Exception as exc:  # pragma: no cover - unexpected init failure
        return jsonify({'ok': False, 'error': str(exc)})

    try:
        with server.get_connection() as conn:
            conn.execute('SELECT 1')
        return jsonify({'ok': True, 'db': server.db_path})
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)})

