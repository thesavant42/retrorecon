import atexit
import logging
from typing import Optional, List

import anyio
from mcp.client.session_group import (
    ClientSessionGroup,
    StdioServerParameters,
    SseServerParameters,
    StreamableHttpParameters,
)
from anyio.from_thread import start_blocking_portal, BlockingPortal

from retrorecon.mcp import RetroReconMCPServer, load_config

logger = logging.getLogger(__name__)

_mcp_server: Optional[RetroReconMCPServer] = None
_memory_group: Optional[ClientSessionGroup] = None
_memory_portal: Optional[BlockingPortal] = None


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


def get_memory_group() -> Optional[ClientSessionGroup]:
    """Return the active MCP client session group for memory module."""
    return _memory_group


def stop_mcp_sqlite() -> None:
    """Cleanup the embedded MCP server instance."""
    global _mcp_server
    if _mcp_server is not None:
        _mcp_server.cleanup()
    _mcp_server = None
    _stop_memory_module()


atexit.register(stop_mcp_sqlite)


def _start_memory_module(cfg) -> None:
    """Launch the memory MCP module if configured and announce its tools."""
    global _memory_group, _memory_portal
    if _memory_group is not None:
        return
    servers = cfg.mcp_servers or []
    mem = next((s for s in servers if s.get("name") == "memory"), None)
    if not mem:
        return
    transport = mem.get("transport", "stdio")
    cmd: List[str] = mem.get("command") or []
    try:
        if transport == "stdio":
            if not cmd:
                return
            params = StdioServerParameters(command=cmd[0], args=cmd[1:])
        elif transport == "sse":
            params = SseServerParameters(
                url=mem.get("url", ""),
                headers=mem.get("headers"),
                timeout=mem.get("timeout", 5),
                sse_read_timeout=mem.get("sse_read_timeout", 300),
            )
        else:
            params = StreamableHttpParameters(
                url=mem.get("url", ""),
                headers=mem.get("headers"),
                timeout=mem.get("timeout", 30),
                sse_read_timeout=mem.get("sse_read_timeout", 300),
            )

        portal = start_blocking_portal()
        group = ClientSessionGroup()
        portal.call(group.__aenter__)
        portal.call(group.connect_to_server, params)
        tools = list(group.tools.keys())
        _memory_group = group
        _memory_portal = portal
        target = " ".join(cmd) if transport == "stdio" else mem.get("url", "")
        logger.debug("Memory MCP module started: %s", target)
        if tools:
            logger.debug("Memory MCP tools: %s", ", ".join(tools))
    except FileNotFoundError:
        logger.error("Memory MCP command not found: %s", " ".join(cmd))
    except Exception as exc:
        logger.error("Failed to start memory MCP module: %s", exc)


def _stop_memory_module() -> None:
    """Terminate the memory MCP client if running."""
    global _memory_group, _memory_portal
    if _memory_group is None or _memory_portal is None:
        return
    try:
        _memory_portal.call(_memory_group.__aexit__, None, None, None)
    except Exception:
        pass
    finally:
        logger.debug("Memory MCP module stopped")
        _memory_group = None
        if _memory_portal is not None:
            _memory_portal.stop()
            _memory_portal = None
