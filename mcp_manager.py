import os
import sys
import subprocess
import atexit
from typing import Optional

# The server currently communicates over stdio only so no port is needed.

_mcp_proc: Optional[subprocess.Popen] = None


def start_mcp_sqlite(db_path: str) -> None:
    """Start the mcp-sqlite server for *db_path*.

    The vendored server communicates over standard input/output. Earlier
    versions exposed a ``port`` argument but no network listener is currently
    started.
    """
    global _mcp_proc
    stop_mcp_sqlite()
    mcp_dir = os.path.join(os.path.dirname(__file__), 'external', 'mcp-sqlite')
    env = os.environ.copy()
    env.setdefault('PYTHONPATH', os.path.join(mcp_dir, 'src'))
    cmd = [sys.executable, '-m', 'mcp_server_sqlite', '--db-path', db_path]
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
