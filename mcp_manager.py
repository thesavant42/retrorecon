import atexit
import logging
import sys
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

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


@dataclass
class ModuleStatus:
    """Status information for an MCP module."""
    name: str
    enabled: bool
    running: bool
    transport: str
    last_started: Optional[float] = None
    last_error: Optional[str] = None
    health_check_url: Optional[str] = None
    tools: list[str] = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = []


@dataclass
class ModuleSpec:
    name: str
    transport: str = "stdio"
    command: list[str] | None = None
    url: str | None = None
    headers: Dict[str, str] | None = None
    timeout: int | None = None
    sse_read_timeout: int | None = None
    enabled: bool = True
    lazy_start: bool = False
    retry: Dict[str, Any] | None = None
    health_check_url: str | None = None


class MCPModuleManager:
    """Manage multiple MCP module client connections."""

    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.modules: Dict[str, ModuleSpec] = {}
        for mod in cfg.mcp_servers or []:
            try:
                spec = ModuleSpec(**mod)
            except TypeError:
                spec = ModuleSpec(
                    name=mod.get("name", ""),
                    transport=mod.get("transport", "stdio"),
                    command=mod.get("command"),
                    url=mod.get("url"),
                    headers=mod.get("headers"),
                    timeout=mod.get("timeout"),
                    sse_read_timeout=mod.get("sse_read_timeout"),
                    enabled=mod.get("enabled", True),
                    lazy_start=mod.get("lazy_start", False),
                    retry=mod.get("retry"),
                    health_check_url=mod.get("health_check_url"),
                )
            self.modules[spec.name] = spec
        self.groups: Dict[str, Optional[ClientSessionGroup]] = {n: None for n in self.modules}
        self.portals: Dict[str, Optional[BlockingPortal]] = {n: None for n in self.modules}
        self.portal_cms: Dict[str, Optional[Any]] = {n: None for n in self.modules}
        self.module_start_times: Dict[str, float] = {}
        self.module_last_errors: Dict[str, str] = {}

    def start_all(self) -> None:
        for name, spec in self.modules.items():
            if spec.enabled and not spec.lazy_start:
                self.start(name)

    def start(self, name: str) -> None:
        if self.groups.get(name) is not None:
            return
        spec = self.modules.get(name)
        if not spec or not spec.enabled:
            return
        
        # Get retry configuration
        retry_config = spec.retry or {}
        max_attempts = retry_config.get("attempts", 3)
        retry_delay = retry_config.get("delay", 1)
        
        last_exception = None
        for attempt in range(max_attempts):
            try:
                params = self._create_params(spec)
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

                group = portal.call(_initialize)
                
                # Success - break out of retry loop
                tools = list(group.tools.keys())
                self.groups[name] = group
                self.portals[name] = portal
                self.portal_cms[name] = portal_ctx
                self.module_start_times[name] = time.time()
                self.module_last_errors.pop(name, None)  # Clear any previous error
                target = " ".join(spec.command or []) if spec.transport == "stdio" else spec.url or ""
                logger.debug("%s MCP module started: %s", spec.name.capitalize(), target)
                if tools:
                    logger.debug("%s MCP tools: %s", spec.name.capitalize(), ", ".join(tools))
                if attempt > 0:
                    logger.info("%s MCP module started after %d attempts", spec.name.capitalize(), attempt + 1)
                return
                
            except FileNotFoundError as exc:
                last_exception = exc
                self.module_last_errors[name] = f"Command not found: {' '.join(spec.command or [])}"
                logger.error("MCP module command not found: %s", " ".join(spec.command or []))
                try:
                    if portal_ctx is not None:
                        portal_ctx.__exit__(None, None, None)
                    else:
                        portal.stop()
                except BaseException:
                    pass
                # FileNotFoundError is not recoverable, don't retry
                return
            except BaseException as exc:
                last_exception = exc
                self.module_last_errors[name] = str(exc)
                try:
                    if portal_ctx is not None:
                        portal_ctx.__exit__(None, None, None)
                    else:
                        portal.stop()
                except BaseException:
                    pass
                
                if attempt < max_attempts - 1:
                    logger.warning("Failed to start %s MCP module (attempt %d/%d): %s. Retrying in %d seconds...", 
                                 spec.name, attempt + 1, max_attempts, exc, retry_delay)
                    time.sleep(retry_delay)
                else:
                    logger.error("Failed to start %s MCP module after %d attempts: %s", 
                               spec.name, max_attempts, exc)
                    return

    def stop(self, name: str) -> None:
        group = self.groups.get(name)
        portal = self.portals.get(name)
        portal_ctx = self.portal_cms.get(name)
        if group is None or portal is None:
            return
        try:
            portal.call(group.__aexit__, None, None, None)
        except BaseException:
            pass
        finally:
            logger.debug("%s MCP module stopped", name.capitalize())
            self.groups[name] = None
            self.module_start_times.pop(name, None)
            if portal_ctx is not None:
                portal_ctx.__exit__(None, None, None)
            elif portal is not None:
                portal.stop()
            self.portals[name] = None
            self.portal_cms[name] = None

    def stop_all(self) -> None:
        for name in list(self.modules.keys()):
            self.stop(name)

    def restart(self, name: str) -> None:
        """Restart a specific module."""
        self.stop(name)
        self.start(name)

    def get_module_status(self, name: str) -> Optional[ModuleStatus]:
        """Get the status of a specific module."""
        spec = self.modules.get(name)
        if not spec:
            return None
        
        group = self.groups.get(name)
        is_running = group is not None
        tools = list(group.tools.keys()) if group else []
        
        return ModuleStatus(
            name=name,
            enabled=spec.enabled,
            running=is_running,
            transport=spec.transport,
            last_started=self.module_start_times.get(name),
            last_error=self.module_last_errors.get(name),
            health_check_url=spec.health_check_url,
            tools=tools
        )

    def get_all_module_status(self) -> Dict[str, ModuleStatus]:
        """Get the status of all modules."""
        result = {}
        for name in self.modules:
            status = self.get_module_status(name)
            if status:
                result[name] = status
        return result

    def check_module_health(self, name: str) -> bool:
        """Check if a module is healthy."""
        group = self.groups.get(name)
        if not group:
            return False
        
        try:
            # Basic health check: try to list tools
            tools = list(group.tools.keys())
            return True
        except Exception as exc:
            logger.warning("Health check failed for %s: %s", name, exc)
            self.module_last_errors[name] = f"Health check failed: {exc}"
            return False

    def check_all_health(self) -> Dict[str, bool]:
        """Check the health of all running modules."""
        result = {}
        for name in self.modules:
            if self.groups.get(name):
                result[name] = self.check_module_health(name)
        return result

    def restart_unhealthy_modules(self) -> list[str]:
        """Restart any unhealthy modules and return the list of restarted modules."""
        restarted = []
        health_status = self.check_all_health()
        
        for name, is_healthy in health_status.items():
            if not is_healthy:
                logger.info("Restarting unhealthy module: %s", name)
                self.restart(name)
                restarted.append(name)
        
        return restarted

    def get_group(self, name: str) -> Optional[ClientSessionGroup]:
        group = self.groups.get(name)
        spec = self.modules.get(name)
        if group is None and spec and spec.enabled and spec.lazy_start:
            self.start(name)
            group = self.groups.get(name)
        return group

    @staticmethod
    def _create_params(spec: ModuleSpec):
        if spec.transport == "stdio":
            cmd = spec.command or []
            if not cmd:
                raise FileNotFoundError()
            if len(cmd) >= 3 and cmd[1] == "-m":
                import importlib.util
                if importlib.util.find_spec(cmd[2]) is None:
                    raise FileNotFoundError(f"MCP module not installed: {cmd[2]}")
            return StdioServerParameters(command=cmd[0], args=cmd[1:])
        elif spec.transport == "sse":
            return SseServerParameters(
                url=spec.url or "",
                headers=spec.headers,
                timeout=spec.timeout or 5,
                sse_read_timeout=spec.sse_read_timeout or 300,
            )
        else:
            return StreamableHttpParameters(
                url=spec.url or "",
                headers=spec.headers,
                timeout=spec.timeout or 30,
                sse_read_timeout=spec.sse_read_timeout or 300,
            )


_mcp_server: Optional[RetroReconMCPServer] = None
_module_manager: Optional[MCPModuleManager] = None


def start_mcp_sqlite(db_path: str) -> RetroReconMCPServer:
    """Initialize or update the embedded MCP server for *db_path*."""
    global _mcp_server, _module_manager
    if _mcp_server is None:
        cfg = load_config()
        cfg.db_path = db_path
        _mcp_server = RetroReconMCPServer(config=cfg)
        _module_manager = MCPModuleManager(cfg)
        _module_manager.start_all()
    else:
        _mcp_server.update_database_path(db_path)
    return _mcp_server


def get_mcp_server() -> Optional[RetroReconMCPServer]:
    """Return the active MCP server instance, if any."""
    return _mcp_server


def get_module_manager() -> Optional[MCPModuleManager]:
    return _module_manager


def get_memory_group() -> Optional[ClientSessionGroup]:
    manager = get_module_manager()
    if manager is not None:
        return manager.get_group("memory")
    return None


def get_fetch_group() -> Optional[ClientSessionGroup]:
    manager = get_module_manager()
    if manager is not None:
        return manager.get_group("fetch")
    return None


def stop_mcp_sqlite() -> None:
    """Cleanup the embedded MCP server instance."""
    global _mcp_server, _module_manager
    if _mcp_server is not None:
        _mcp_server.cleanup()
    _mcp_server = None
    if _module_manager is not None:
        _module_manager.stop_all()
    _module_manager = None


def _atexit_stop() -> None:
    stop_mcp_sqlite()


atexit.register(_atexit_stop)
