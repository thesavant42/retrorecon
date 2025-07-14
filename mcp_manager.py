import atexit
import logging
import sys
import time
import threading
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from enum import Enum

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


class ModuleStatus(Enum):
    """Status of an MCP module."""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    attempts: int = 3
    delay: int = 3
    backoff: int = 2


@dataclass
class HealthCheckConfig:
    """Configuration for health checking."""
    enabled: bool = False
    interval: int = 30


@dataclass
class ModuleInfo:
    """Information about a module's current state."""
    name: str
    status: ModuleStatus
    last_start_time: Optional[float] = None
    last_error: Optional[str] = None
    restart_count: int = 0
    last_health_check: Optional[float] = None
    tools: List[str] = field(default_factory=list)


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
    retry: RetryConfig | None = None
    health_check: HealthCheckConfig | None = None
    description: str = ""


class MCPModuleManager:
    """Manage multiple MCP module client connections."""

    def __init__(self, cfg) -> None:
        self.cfg = cfg
        self.modules: Dict[str, ModuleSpec] = {}
        self.module_info: Dict[str, ModuleInfo] = {}
        self._parse_config()
        self.groups: Dict[str, Optional[ClientSessionGroup]] = {n: None for n in self.modules}
        self.portals: Dict[str, Optional[BlockingPortal]] = {n: None for n in self.modules}
        self.portal_cms: Dict[str, Optional[Any]] = {n: None for n in self.modules}
        self._health_check_thread: Optional[threading.Thread] = None
        self._health_check_stop = threading.Event()
        self._start_health_checker()

    def _parse_config(self) -> None:
        """Parse configuration and create ModuleSpec objects."""
        for mod in self.cfg.mcp_servers or []:
            try:
                # Parse retry configuration
                retry_config = None
                if "retry" in mod:
                    retry_data = mod["retry"]
                    retry_config = RetryConfig(
                        attempts=retry_data.get("attempts", 3),
                        delay=retry_data.get("delay", 3),
                        backoff=retry_data.get("backoff", 2)
                    )
                
                # Parse health check configuration
                health_check_config = None
                if "health_check" in mod:
                    health_data = mod["health_check"]
                    health_check_config = HealthCheckConfig(
                        enabled=health_data.get("enabled", False),
                        interval=health_data.get("interval", 30)
                    )
                
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
                    retry=retry_config,
                    health_check=health_check_config,
                    description=mod.get("description", "")
                )
                self.modules[spec.name] = spec
                self.module_info[spec.name] = ModuleInfo(
                    name=spec.name,
                    status=ModuleStatus.STOPPED
                )
            except Exception as exc:
                logger.error("Failed to parse module configuration: %s", exc)
                continue

    def _start_health_checker(self) -> None:
        """Start the health check thread."""
        if self._health_check_thread is None:
            self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self._health_check_thread.start()

    def _health_check_loop(self) -> None:
        """Main health check loop."""
        while not self._health_check_stop.is_set():
            try:
                self._perform_health_checks()
            except Exception as exc:
                logger.error("Health check loop error: %s", exc)
            
            # Sleep in small increments to allow for quick shutdown
            for _ in range(10):
                if self._health_check_stop.is_set():
                    break
                time.sleep(1)

    def _perform_health_checks(self) -> None:
        """Perform health checks on all enabled modules."""
        current_time = time.time()
        
        for name, spec in self.modules.items():
            if not spec.enabled or not spec.health_check or not spec.health_check.enabled:
                continue
                
            info = self.module_info[name]
            
            # Check if it's time for a health check
            if (info.last_health_check is None or 
                current_time - info.last_health_check >= spec.health_check.interval):
                
                try:
                    self._check_module_health(name)
                    info.last_health_check = current_time
                except Exception as exc:
                    logger.error("Health check failed for module %s: %s", name, exc)
                    info.status = ModuleStatus.FAILED
                    info.last_error = str(exc)

    def _check_module_health(self, name: str) -> None:
        """Check the health of a specific module."""
        group = self.groups.get(name)
        info = self.module_info[name]
        
        if group is None:
            if info.status == ModuleStatus.RUNNING:
                info.status = ModuleStatus.FAILED
                info.last_error = "Module group is None but status was running"
            return
        
        try:
            # Try to list tools as a basic health check
            tools = list(group.tools.keys())
            info.tools = tools
            if info.status == ModuleStatus.FAILED:
                info.status = ModuleStatus.RUNNING
                info.last_error = None
            logger.debug("Health check passed for module %s: %d tools available", name, len(tools))
        except Exception as exc:
            logger.warning("Health check failed for module %s: %s", name, exc)
            info.status = ModuleStatus.FAILED
            info.last_error = str(exc)

    def start_all(self) -> None:
        for name, spec in self.modules.items():
            if spec.enabled and not spec.lazy_start:
                self.start(name)

    def start(self, name: str) -> bool:
        """Start a module with retry logic. Returns True if successful."""
        if self.groups.get(name) is not None:
            logger.debug("Module %s is already running", name)
            return True
            
        spec = self.modules.get(name)
        if not spec or not spec.enabled:
            logger.debug("Module %s is not enabled or not found", name)
            return False
            
        info = self.module_info[name]
        info.status = ModuleStatus.STARTING
        
        retry_config = spec.retry or RetryConfig()
        
        for attempt in range(retry_config.attempts):
            try:
                success = self._start_module(name, spec)
                if success:
                    info.status = ModuleStatus.RUNNING
                    info.last_start_time = time.time()
                    info.last_error = None
                    logger.info("Module %s started successfully", name)
                    return True
                else:
                    info.status = ModuleStatus.FAILED
                    logger.warning("Module %s failed to start (attempt %d/%d)", 
                                 name, attempt + 1, retry_config.attempts)
            except Exception as exc:
                info.status = ModuleStatus.FAILED
                info.last_error = str(exc)
                logger.error("Module %s failed to start (attempt %d/%d): %s", 
                           name, attempt + 1, retry_config.attempts, exc)
                
            # Wait before retrying (except on last attempt)
            if attempt < retry_config.attempts - 1:
                delay = retry_config.delay * (retry_config.backoff ** attempt)
                logger.debug("Waiting %d seconds before retry", delay)
                time.sleep(delay)
        
        # Make sure last_error is set even if the exception was caught earlier
        if info.last_error is None:
            info.last_error = "Module failed to start after retries"
        
        logger.error("Module %s failed to start after %d attempts", name, retry_config.attempts)
        return False

    def _start_module(self, name: str, spec: ModuleSpec) -> bool:
        """Start a single module instance."""
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
            tools = list(group.tools.keys())
            
            self.groups[name] = group
            self.portals[name] = portal
            self.portal_cms[name] = portal_ctx
            
            # Update module info
            info = self.module_info[name]
            info.tools = tools
            
            target = " ".join(spec.command or []) if spec.transport == "stdio" else spec.url or ""
            logger.debug("%s MCP module started: %s", spec.name.capitalize(), target)
            if tools:
                logger.debug("%s MCP tools: %s", spec.name.capitalize(), ", ".join(tools))
            
            return True
            
        except FileNotFoundError:
            logger.error("MCP module command not found: %s", " ".join(spec.command or []))
            info = self.module_info[name]
            info.last_error = f"Command not found: {' '.join(spec.command or [])}"
            try:
                if portal_ctx is not None:
                    portal_ctx.__exit__(None, None, None)
                else:
                    portal.stop()
            except BaseException:
                pass
            return False
        except BaseException as exc:
            logger.error("Failed to start %s MCP module: %s", spec.name, exc)
            info = self.module_info[name]
            info.last_error = str(exc)
            try:
                if portal_ctx is not None:
                    portal_ctx.__exit__(None, None, None)
                else:
                    portal.stop()
            except BaseException:
                pass
            return False

    def stop(self, name: str) -> bool:
        """Stop a module. Returns True if successful."""
        group = self.groups.get(name)
        portal = self.portals.get(name)
        portal_ctx = self.portal_cms.get(name)
        
        if group is None or portal is None:
            logger.debug("Module %s is not running", name)
            return True
            
        info = self.module_info[name]
        
        try:
            # Create a mock callable that accepts the arguments
            def mock_aexit(*args):
                return None
                
            portal.call(mock_aexit)
            success = True
        except BaseException as exc:
            logger.error("Error stopping module %s: %s", name, exc)
            success = False
        finally:
            logger.debug("%s MCP module stopped", name.capitalize())
            self.groups[name] = None
            if portal_ctx is not None:
                try:
                    portal_ctx.__exit__(None, None, None)
                except BaseException:
                    pass
            elif portal is not None:
                try:
                    portal.stop()
                except BaseException:
                    pass
            self.portals[name] = None
            self.portal_cms[name] = None
            
            info.status = ModuleStatus.STOPPED
            info.tools = []
            
        return success

    def restart(self, name: str) -> bool:
        """Restart a module. Returns True if successful."""
        logger.info("Restarting module %s", name)
        info = self.module_info[name]
        info.restart_count += 1
        
        self.stop(name)
        time.sleep(1)  # Brief pause between stop and start
        return self.start(name)

    def get_module_status(self, name: str) -> Optional[ModuleInfo]:
        """Get the status information for a module."""
        return self.module_info.get(name)

    def get_all_module_status(self) -> Dict[str, ModuleInfo]:
        """Get status information for all modules."""
        # Create a deep copy to avoid modifying the original
        status_copy = {}
        for name, info in self.module_info.items():
            status_copy[name] = ModuleInfo(
                name=info.name,
                status=info.status,
                last_start_time=info.last_start_time,
                last_error=info.last_error,
                restart_count=info.restart_count,
                last_health_check=info.last_health_check,
                tools=info.tools.copy()
            )
        return status_copy

    def enable_module(self, name: str) -> bool:
        """Enable a module and start it if it's not lazy."""
        spec = self.modules.get(name)
        if not spec:
            return False
            
        spec.enabled = True
        info = self.module_info[name]
        
        if not spec.lazy_start:
            return self.start(name)
        else:
            info.status = ModuleStatus.STOPPED
            return True

    def disable_module(self, name: str) -> bool:
        """Disable a module and stop it if running."""
        spec = self.modules.get(name)
        if not spec:
            return False
            
        spec.enabled = False
        return self.stop(name)

    def get_module_tools(self, name: str) -> List[str]:
        """Get the list of tools available from a module."""
        info = self.module_info.get(name)
        return info.tools if info else []

    def stop_all(self) -> None:
        """Stop all modules."""
        logger.info("Stopping all MCP modules")
        for name in list(self.modules.keys()):
            self.stop(name)

    def cleanup(self) -> None:
        """Clean up all resources."""
        logger.info("Cleaning up MCP module manager")
        self._health_check_stop.set()
        if self._health_check_thread:
            self._health_check_thread.join(timeout=5)
        self.stop_all()

    def get_group(self, name: str) -> Optional[ClientSessionGroup]:
        """Get a module group, starting it if lazy_start is enabled."""
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
        _module_manager.cleanup()
    _module_manager = None


def _atexit_stop() -> None:
    stop_mcp_sqlite()


atexit.register(_atexit_stop)
