import os
import os
import sys
import subprocess
import atexit
from typing import Optional

from retrorecon.mcp import RetroReconMCPServer, load_config

MCP_PORT = 12345
_mcp_proc: Optional[subprocess.Popen] = None
_mcp_server: Optional[RetroReconMCPServer] = None


def start_mcp_sqlite(db_path: str, port: int = MCP_PORT) -> RetroReconMCPServer:
    """Start the mcp-sqlite server for *db_path* on the given port."""
    global _mcp_proc, _mcp_server
    stop_mcp_sqlite()
    mcp_dir = os.path.join(os.path.dirname(__file__), 'external', 'mcp-sqlite')
    env = os.environ.copy()
    env.setdefault('PYTHONPATH', os.path.join(mcp_dir, 'src'))
    cmd = [sys.executable, '-m', 'mcp_server_sqlite', '--db-path', db_path,
           '--host', '127.0.0.1', '--port', str(port)]
    _mcp_proc = subprocess.Popen(cmd, cwd=mcp_dir, env=env)

    cfg = load_config()
    cfg.db_path = db_path
    _mcp_server = RetroReconMCPServer(config=cfg)
    return _mcp_server


def stop_mcp_sqlite() -> None:
    """Stop the running mcp-sqlite subprocess and cleanup the server."""
    global _mcp_proc, _mcp_server
    if _mcp_proc is not None and _mcp_proc.poll() is None:
        _mcp_proc.terminate()
        try:
            _mcp_proc.wait(timeout=5)
        except Exception:
            _mcp_proc.kill()
    _mcp_proc = None
    if _mcp_server is not None:
        _mcp_server.cleanup()
    _mcp_server = None


atexit.register(stop_mcp_sqlite)
