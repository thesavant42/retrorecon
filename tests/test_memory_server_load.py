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

    class DummyGroup:
        async def __aenter__(self):
            captured['entered'] = True
            return self

        async def __aexit__(self, exc_type, exc, tb):
            captured['exited'] = True

        async def connect_to_server(self, params):
            captured['command'] = params.command
            captured['args'] = params.args

        @property
        def tools(self):
            return {}

    monkeypatch.setattr(mcp_manager, 'ClientSessionGroup', lambda: DummyGroup())

    monkeypatch.setattr(mcp_manager.anyio, 'run', lambda func: asyncio.run(func()))
    mcp_manager.stop_mcp_sqlite()

    mcp_manager.start_mcp_sqlite(str(tmp_path / "db.sqlite"))
    assert captured['command'] == "basic-memory"
    assert captured['args'] == ["mcp", "--transport", "stdio"]
    mcp_manager.stop_mcp_sqlite()
    monkeypatch.delenv("RETRORECON_MCP_SERVERS_FILE")
