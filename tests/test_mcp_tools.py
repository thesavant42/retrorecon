from retrorecon.mcp.server import RetroReconMCPServer
from retrorecon.mcp.config import load_config


def test_call_tool_returns_type(tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    server = RetroReconMCPServer(config=cfg)
    result = server._call_tool("list_tables", {})
    assert result["type"] == "text"
    assert "text" in result
