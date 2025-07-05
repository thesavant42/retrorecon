import json
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mcp_manager


def test_memory_server_started(monkeypatch, tmp_path):
    cfg_file = tmp_path / "mcp_servers.json"
    cfg_file.write_text(json.dumps([
        {
            "name": "memory",
            "transport": "stdio",
            "command": ["basic-memory", "mcp", "--transport", "stdio"],
        }
    ]))
    monkeypatch.setenv("RETRORECON_MCP_SERVERS_FILE", str(cfg_file))

    captured = {}

    class DummyTransport:
        def __init__(self, command, args):
            captured['command'] = command
            captured['args'] = args

    class DummyClient:
        def __init__(self, transport):
            captured['transport'] = transport
        async def _connect(self):
            pass
        async def list_tools_mcp(self):
            class R:
                tools = []
            return R()

    monkeypatch.setattr(mcp_manager, 'StdioTransport', DummyTransport)
    monkeypatch.setattr(mcp_manager, 'Client', DummyClient)

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def DummyFailAfter(*args, **kwargs):
        yield

    monkeypatch.setattr(mcp_manager.anyio, 'run', lambda func: asyncio.run(func()))
    monkeypatch.setattr(mcp_manager.anyio, 'fail_after', lambda *a, **k: DummyFailAfter())
    mcp_manager.stop_mcp_sqlite()

    mcp_manager.start_mcp_sqlite(str(tmp_path / "db.sqlite"))
    assert captured['command'] == "basic-memory"
    assert captured['args'] == ["mcp", "--transport", "stdio"]
    mcp_manager.stop_mcp_sqlite()
    monkeypatch.delenv("RETRORECON_MCP_SERVERS_FILE")
