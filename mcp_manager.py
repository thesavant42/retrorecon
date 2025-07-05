import atexit
import logging
from typing import Optional, List

import anyio
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from retrorecon.mcp import RetroReconMCPServer, load_config

logger = logging.getLogger(__name__)

_mcp_server: Optional[RetroReconMCPServer] = None
_memory_client: Optional[Client] = None


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
    """Launch the memory MCP module if configured and announce its tools."""
    global _memory_client
    if _memory_client is not None:
        return
    servers = cfg.mcp_servers or []
    mem = next((s for s in servers if s.get("name") == "memory"), None)
    if not mem or mem.get("transport") != "stdio":
        return
    cmd: List[str] = mem.get("command") or []
    if not cmd:
        return
    try:
        transport = StdioTransport(command=cmd[0], args=cmd[1:])
        client = Client(transport)

        async def _init_client() -> tuple[Client, List[str]]:
            with anyio.fail_after(10):
                await client._connect()
            tools: List[str] = []
            try:
                with anyio.fail_after(5):
                    result = await client.list_tools_mcp()
                    tools = [t.name for t in result.tools]
            except Exception as exc:
                logger.error("Failed to list memory MCP tools: %s", exc)
            return client, tools

        _memory_client, tools = anyio.run(_init_client)
        logger.debug("Memory MCP module started: %s", cmd)
        if tools:
            logger.debug("Memory MCP tools: %s", ", ".join(tools))
    except FileNotFoundError:
        logger.error("Memory MCP command not found: %s", cmd)
    except Exception as exc:
        logger.error("Failed to start memory MCP module: %s", exc)


def _stop_memory_module() -> None:
    """Terminate the memory MCP client if running."""
    global _memory_client
    if _memory_client is None:
        return
    try:
        async def _disconnect() -> None:
            with anyio.fail_after(5):
                await _memory_client._disconnect()

        anyio.run(_disconnect)
    except Exception:
        pass
    finally:
        logger.debug("Memory MCP module stopped")
        _memory_client = None
