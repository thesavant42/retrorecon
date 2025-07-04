import atexit
from typing import Optional

from retrorecon.mcp import RetroReconMCPServer, load_config

_mcp_server: Optional[RetroReconMCPServer] = None


def start_mcp_sqlite(db_path: str) -> RetroReconMCPServer:
    """Initialize or update the embedded MCP server for *db_path*."""
    global _mcp_server
    if _mcp_server is None:
        cfg = load_config()
        cfg.db_path = db_path
        _mcp_server = RetroReconMCPServer(config=cfg)
    else:
        _mcp_server.update_database_path(db_path)
    return _mcp_server


def get_mcp_server() -> Optional[RetroReconMCPServer]:
    """Return the active MCP server instance, if any."""
    return _mcp_server


def stop_mcp_sqlite() -> None:
    """Cleanup the embedded MCP server instance."""
    global _mcp_server
    if _mcp_server is not None:
        _mcp_server.cleanup()
    _mcp_server = None


atexit.register(stop_mcp_sqlite)
