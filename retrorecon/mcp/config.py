import os
from dataclasses import dataclass, field
from typing import Optional
import json

from fastmcp.utilities.mcp_config import MCPConfig as MCPServersConfig

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
    mcp_servers: MCPServersConfig | None = None


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

    servers_env = os.getenv("RETRORECON_MCP_SERVERS")
    if servers_env:
        try:
            servers_cfg = MCPServersConfig.from_dict(json.loads(servers_env))
        except Exception:
            servers_cfg = None
    else:
        servers_cfg = MCPServersConfig.from_dict({
            "memory": {
                "command": "npx",
                "args": ["-y", "--silent", "@modelcontextprotocol/server-memory"],
                "env": {"MEMORY_FILE_PATH": "/sandbox/memory.json"}
            },
            "sequential-thinking": {
                "command": "npx",
                "args": ["-y", "--silent", "@modelcontextprotocol/server-sequential-thinking"]
            },
            "time": {
                "command": "uvx",
                "args": ["mcp-server-time"],
                "env": {"TZ": "America/Los_Angeles"}
            }
        })
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
