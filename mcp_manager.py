import os
import sys
import subprocess
import atexit
from typing import Optional

MCP_PORT = 12345
_mcp_proc: Optional[subprocess.Popen] = None


def start_mcp_sqlite(db_path: str, port: int = MCP_PORT) -> None:
    """Start the mcp-sqlite server for *db_path* on the given port."""
    global _mcp_proc
    stop_mcp_sqlite()
    mcp_dir = os.path.join(os.path.dirname(__file__), 'external', 'mcp-sqlite')
    env = os.environ.copy()
    env.setdefault('PYTHONPATH', os.path.join(mcp_dir, 'src'))
    cmd = [sys.executable, '-m', 'mcp_server_sqlite', '--db-path', db_path,
           '--host', '127.0.0.1', '--port', str(port)]
    _mcp_proc = subprocess.Popen(cmd, cwd=mcp_dir, env=env)


def stop_mcp_sqlite() -> None:
    """Stop the running mcp-sqlite subprocess if active."""
    global _mcp_proc
    if _mcp_proc is not None and _mcp_proc.poll() is None:
        _mcp_proc.terminate()
        try:
            _mcp_proc.wait(timeout=5)
        except Exception:
            _mcp_proc.kill()
    _mcp_proc = None


atexit.register(stop_mcp_sqlite)
