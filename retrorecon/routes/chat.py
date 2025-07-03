import app
from flask import Blueprint, request, jsonify

from retrorecon.mcp.server import RetroReconMCPServer

bp = Blueprint('chat', __name__, url_prefix='/chat')


def _get_server() -> RetroReconMCPServer:
    """Get or create the MCP server instance."""
    server = getattr(app, 'mcp_server', None)
    if server is None:
        server = RetroReconMCPServer()
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

    The user sends plain English questions. The MCP server uses a language model
    to translate the question into SQL and execute it. Direct SQL input from the
    user is not required or expected.
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
