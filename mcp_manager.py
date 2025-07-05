import atexit
import subprocess
import logging
from typing import Optional

from retrorecon.mcp import RetroReconMCPServer, load_config

logger = logging.getLogger(__name__)

_mcp_server: Optional[RetroReconMCPServer] = None
_memory_proc: Optional[subprocess.Popen] = None


def start_mcp_sqlite(db_path: str) -> RetroReconMCPServer:
    """Initialize or update the embedded MCP server for *db_path*."""
    global _mcp_server
    if _mcp_server is None:
        cfg = load_config()
        cfg.db_path = db_path
        _mcp_server = RetroReconMCPServer(config=cfg)
        _start_memory_module(cfg)
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
    _stop_memory_module()


atexit.register(stop_mcp_sqlite)


def _start_memory_module(cfg) -> None:
    """Launch the memory MCP module if configured."""
    global _memory_proc
    if _memory_proc is not None:
        return
    servers = cfg.mcp_servers or []
    mem = next((s for s in servers if s.get("name") == "memory"), None)
    if not mem or mem.get("transport") != "stdio":
        return
    cmd = mem.get("command")
    if not cmd:
        return
    try:
        _memory_proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        logger.debug("Memory MCP module started: %s", cmd)
    except FileNotFoundError:
        logger.error("Memory MCP command not found: %s", cmd)
    except Exception as exc:
        logger.error("Failed to start memory MCP module: %s", exc)


def _stop_memory_module() -> None:
    """Terminate the memory MCP process if running."""
    global _memory_proc
    if _memory_proc is None:
        return
    try:
        _memory_proc.terminate()
        _memory_proc.wait(timeout=5)
    except Exception:
        if _memory_proc.poll() is None:
            _memory_proc.kill()
    finally:
        logger.debug("Memory MCP module stopped")
        _memory_proc = None
