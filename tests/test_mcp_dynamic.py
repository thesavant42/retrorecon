import pytest
from retrorecon.mcp.server import RetroReconMCPServer
from retrorecon.mcp.config import load_config
from fastmcp import FastMCP
from fastmcp.tools import FunctionTool
from mcp.types import TextContent


@pytest.fixture
def base_server(tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    cfg.mcp_servers = None
    return RetroReconMCPServer(config=cfg)


def make_child():
    child = FastMCP("child")

    async def hi() -> TextContent:
        return TextContent(type="text", text="hi")

    child.add_tool(FunctionTool.from_function(hi, name="hi", description="say hi"))
    return child


def test_tools_include_mounted(base_server):
    child = make_child()
    base_server.server.mount(child, prefix="child")
    tools = base_server._openai_tools()
    names = {t["function"]["name"] for t in tools}
    assert "child_hi" in names
    assert "read_query" in names


def test_routing_to_mounted(base_server):
    child = make_child()
    base_server.server.mount(child, prefix="child")
    result = base_server._call_tool("child_hi", {})
    assert result["type"] == "text"
    assert "hi" in result["text"]


def test_dynamic_addition(base_server):
    initial = set(t["function"]["name"] for t in base_server._openai_tools())
    child = make_child()
    base_server.server.mount(child, prefix="child")
    updated = set(t["function"]["name"] for t in base_server._openai_tools())
    assert "child_hi" in updated - initial
