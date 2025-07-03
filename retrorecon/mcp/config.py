import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class MCPConfig:
    """Configuration values for the MCP server."""

    db_path: Optional[str] = None
    model: str = "gpt-4o"
    row_limit: int = 100


def load_config() -> MCPConfig:
    """Load MCP configuration from environment variables."""
    db_path = os.getenv("RETRORECON_MCP_DB")
    model = os.getenv("RETRORECON_MCP_MODEL", "gpt-4o")
    try:
        row_limit = int(os.getenv("RETRORECON_MCP_ROW_LIMIT", "100"))
    except ValueError:
        row_limit = 100
    return MCPConfig(db_path=db_path, model=model, row_limit=row_limit)
