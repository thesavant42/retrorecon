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
    api_base: str = "http://localhost:1234/v1"
    model: str = "qwen2.5-coldbrew-aetheria-test2_tools"
    temperature: float = 0.1
    row_limit: int = 100
    api_key: Optional[str] = None
    timeout: int = 20
    alt_api_bases: list[str] = field(default_factory=list)
    mcp_servers: List[Dict[str, object]] | None = None


def load_config() -> MCPConfig:
    """Load MCP configuration from environment variables."""
    db_path = os.getenv("RETRORECON_MCP_DB")
    api_base = os.getenv("RETRORECON_MCP_API_BASE", "http://localhost:1234/v1")
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
        timeout = int(os.getenv("RETRORECON_MCP_TIMEOUT", "20"))
    except ValueError:
        timeout = 20
    alt_env = os.getenv("RETRORECON_MCP_ALT_API_BASES", "")
    alt_api_bases = [b.strip() for b in alt_env.split(",") if b.strip()]

    servers_cfg = None
    cfg_file = os.getenv("RETRORECON_MCP_SERVERS_FILE", "mcp_servers.json")
    if os.path.exists(cfg_file):
        try:
            with open(cfg_file, "r", encoding="utf-8") as fh:
                servers_cfg = json.load(fh)
        except Exception as exc:
            logger.error("Failed to load MCP server config: %s", exc)
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
    )
