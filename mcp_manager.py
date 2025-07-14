import atexit
import logging
import sys
from typing import Optional, List, Any

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
# Active MCP server for memory module
_memory_group: Optional[ClientSessionGroup] = None
_memory_portal: Optional[BlockingPortal] = None
# Optional context manager returned by ``start_blocking_portal``.
_memory_portal_cm: Optional[Any] = None

# Active MCP server for fetch module
_fetch_group: Optional[ClientSessionGroup] = None
_fetch_portal: Optional[BlockingPortal] = None
# Optional context manager returned by ``start_blocking_portal`` for fetch module
_fetch_portal_cm: Optional[Any] = None


def start_mcp_sqlite(db_path: str) -> RetroReconMCPServer:
    """Initialize or update the embedded MCP server for *db_path*."""
    global _mcp_server
    if _mcp_server is None:
        cfg = load_config()
        cfg.db_path = db_path
        _mcp_server = RetroReconMCPServer(config=cfg)
        _start_memory_module(cfg)
        _start_fetch_module(cfg)
    else:
        _mcp_server.update_database_path(db_path)
    return _mcp_server


def get_mcp_server() -> Optional[RetroReconMCPServer]:
    """Return the active MCP server instance, if any."""
    return _mcp_server


def get_memory_group() -> Optional[ClientSessionGroup]:
    """Return the active MCP client session group for memory module."""
    return _memory_group


def get_fetch_group() -> Optional[ClientSessionGroup]:
    """Return the active MCP client session group for fetch module."""
    return _fetch_group


def stop_mcp_sqlite() -> None:
    """Cleanup the embedded MCP server instance."""
    global _mcp_server
    if _mcp_server is not None:
        _mcp_server.cleanup()
    _mcp_server = None
    _stop_memory_module()
    _stop_fetch_module()


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
            if len(cmd) >= 3 and cmd[1] == "-m":
                import importlib.util
                if importlib.util.find_spec(cmd[2]) is None:
                    logger.error("MCP module not installed: %s", cmd[2])
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

        portal_ctx = start_blocking_portal()
        # ``start_blocking_portal`` returns a context manager in normal usage.
        # Test suites may monkeypatch it to return a plain portal instance, so
        # handle both cases here.
        if hasattr(portal_ctx, "__enter__"):
            portal = portal_ctx.__enter__()
        else:
            portal = portal_ctx
            portal_ctx = None

        async def _initialize() -> ClientSessionGroup:
            group = ClientSessionGroup()
            await group.__aenter__()
            try:
                await group.connect_to_server(params)
            except Exception:
                await group.__aexit__(*sys.exc_info())
                raise
            return group

        try:
            group = portal.call(_initialize)
        except BaseException as exc:
            try:
                if portal_ctx is not None:
                    portal_ctx.__exit__(type(exc), exc, exc.__traceback__)
                else:
                    portal.stop()
            except BaseException:
                pass
            logger.error("Failed to start memory MCP module: %s", exc)
            return
        tools = list(group.tools.keys())
        _memory_group = group
        _memory_portal = portal
        global _memory_portal_cm
        _memory_portal_cm = portal_ctx
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
    global _memory_group, _memory_portal, _memory_portal_cm
    if _memory_group is None or _memory_portal is None:
        return
    try:
        _memory_portal.call(_memory_group.__aexit__, None, None, None)
    except BaseException:
        pass
    finally:
        logger.debug("Memory MCP module stopped")
        _memory_group = None
        if _memory_portal_cm is not None:
            _memory_portal_cm.__exit__(None, None, None)
            _memory_portal_cm = None
        elif _memory_portal is not None:
            _memory_portal.stop()
        _memory_portal = None


def _start_fetch_module(cfg) -> None:
    """Launch the fetch MCP module if configured and announce its tools."""
    global _fetch_group, _fetch_portal
    if _fetch_group is not None:
        return
    servers = cfg.mcp_servers or []
    fetch = next((s for s in servers if s.get("name") == "fetch"), None)
    if not fetch:
        return
    transport = fetch.get("transport", "stdio")
    cmd: List[str] = fetch.get("command") or []
    try:
        if transport == "stdio":
            if not cmd:
                return
            if len(cmd) >= 3 and cmd[1] == "-m":
                import importlib.util
                if importlib.util.find_spec(cmd[2]) is None:
                    logger.error("MCP module not installed: %s", cmd[2])
                    return
            params = StdioServerParameters(command=cmd[0], args=cmd[1:])
        elif transport == "sse":
            params = SseServerParameters(
                url=fetch.get("url", ""),
                headers=fetch.get("headers"),
                timeout=fetch.get("timeout", 5),
                sse_read_timeout=fetch.get("sse_read_timeout", 300),
            )
        else:
            params = StreamableHttpParameters(
                url=fetch.get("url", ""),
                headers=fetch.get("headers"),
                timeout=fetch.get("timeout", 30),
                sse_read_timeout=fetch.get("sse_read_timeout", 300),
            )

        portal_ctx = start_blocking_portal()
        if hasattr(portal_ctx, "__enter__"):
            portal = portal_ctx.__enter__()
        else:
            portal = portal_ctx
            portal_ctx = None

        async def _initialize() -> ClientSessionGroup:
            group = ClientSessionGroup()
            await group.__aenter__()
            try:
                await group.connect_to_server(params)
            except Exception:
                await group.__aexit__(*sys.exc_info())
                raise
            return group

        try:
            group = portal.call(_initialize)
        except BaseException as exc:
            try:
                if portal_ctx is not None:
                    portal_ctx.__exit__(type(exc), exc, exc.__traceback__)
                else:
                    portal.stop()
            except BaseException:
                pass
            logger.error("Failed to start fetch MCP module: %s", exc)
            return
        tools = list(group.tools.keys())
        _fetch_group = group
        _fetch_portal = portal
        global _fetch_portal_cm
        _fetch_portal_cm = portal_ctx
        target = " ".join(cmd) if transport == "stdio" else fetch.get("url", "")
        logger.debug("Fetch MCP module started: %s", target)
        if tools:
            logger.debug("Fetch MCP tools: %s", ", ".join(tools))
    except FileNotFoundError:
        logger.error("Fetch MCP command not found: %s", " ".join(cmd))
    except Exception as exc:
        logger.error("Failed to start fetch MCP module: %s", exc)


def _stop_fetch_module() -> None:
    """Terminate the fetch MCP client if running."""
    global _fetch_group, _fetch_portal, _fetch_portal_cm
    if _fetch_group is None or _fetch_portal is None:
        return
    try:
        _fetch_portal.call(_fetch_group.__aexit__, None, None, None)
    except BaseException:
        pass
    finally:
        logger.debug("Fetch MCP module stopped")
        _fetch_group = None
        if _fetch_portal_cm is not None:
            _fetch_portal_cm.__exit__(None, None, None)
            _fetch_portal_cm = None
        elif _fetch_portal is not None:
            _fetch_portal.stop()
        _fetch_portal = None
