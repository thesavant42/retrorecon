import os
from dataclasses import dataclass, field
from typing import Optional, List, Dict
import json
import logging

logger = logging.getLogger(__name__)
@dataclass
class MCPConfig:
    """Configuration values for the MCP server."""

    db_path: Optional[str] = None
    api_base: str = "http://192.168.1.98:1234/v1"
    model: str = "qwen2.5-coldbrew-aetheria-test2_tools"
    temperature: float = 0.1
    row_limit: int = 100
    api_key: Optional[str] = None
    timeout: int = 60
    alt_api_bases: list[str] = field(default_factory=list)
    mcp_servers: List[Dict[str, object]] | None = None
    servers_file: str | None = None


def load_config() -> MCPConfig:
    """Load MCP configuration from environment variables."""
    db_path = os.getenv("RETRORECON_MCP_DB")
    api_base = os.getenv("RETRORECON_MCP_API_BASE", "http://192.168.1.98:1234/v1")
    if api_base and not api_base.startswith(("http://", "https://")):
        logger.warning("Primary API base missing protocol, adding http://: %s", api_base)
        api_base = "http://" + api_base
    model = os.getenv("RETRORECON_MCP_MODEL", "qwen2.5-coldbrew-aetheria-test2_tools")
    try:
        temperature = float(os.getenv("RETRORECON_MCP_TEMPERATURE", "0.1"))
    except ValueError:
        temperature = 0.1
    api_key = os.getenv("RETRORECON_MCP_API_KEY")
    try:
        row_limit = int(os.getenv("RETRORECON_MCP_ROW_LIMIT", "100"))
    except ValueError:
        row_limit = 100
    try:
        timeout = int(os.getenv("RETRORECON_MCP_TIMEOUT", "60"))
    except ValueError:
        timeout = 60
    alt_env = os.getenv("RETRORECON_MCP_ALT_API_BASES", "")
    alt_api_bases: list[str] = []
    if alt_env:
        parsed: list[str] | str
        try:
            parsed = json.loads(alt_env)
            if isinstance(parsed, list):
                alt_api_bases = [str(b) for b in parsed]
            else:
                alt_api_bases = [str(parsed)]
        except json.JSONDecodeError:
            alt_api_bases = [b.strip() for b in alt_env.split(",") if b.strip()]

    normalized: list[str] = []
    for base in alt_api_bases:
        if not base.startswith(("http://", "https://")):
            logger.warning("Alternative API base missing protocol, adding http://: %s", base)
            base = "http://" + base
        normalized.append(base)
    alt_api_bases = normalized

    servers_cfg = None
    cfg_file = os.getenv("RETRORECON_MCP_SERVERS_FILE", "mcp_servers.json")
    if not os.path.isabs(cfg_file):
        cfg_file = os.path.join(os.getcwd(), cfg_file)
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as fh:
                config_data = json.load(fh)
            # Handle both old format (array) and new format (object with servers array)
            if isinstance(config_data, list):
                servers_cfg = config_data
                logger.debug("Loaded MCP server config (legacy format) from %s", cfg_file)
            elif isinstance(config_data, dict) and "servers" in config_data:
                servers_cfg = config_data["servers"]
                logger.debug("Loaded MCP server config (new format) from %s", cfg_file)
            else:
                logger.error("Invalid MCP server config format in '%s': expected array or object with 'servers' key", cfg_file)
                servers_cfg = []
        except Exception as exc:
            logger.error("Failed to load MCP server config '%s': %s", cfg_file, exc)
            servers_cfg = []
    else:
        logger.debug("MCP server config not found at %s", cfg_file)
    return MCPConfig(
        db_path=db_path,
        api_base=api_base,
        model=model,
        temperature=temperature,
        row_limit=row_limit,
        api_key=api_key,
        timeout=timeout,
        alt_api_bases=alt_api_bases,
        mcp_servers=servers_cfg,
        servers_file=cfg_file,
    )
