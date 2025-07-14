import json
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mcp_manager


def test_fetch_server_started(monkeypatch, tmp_path):
    cfg_file = tmp_path / "mcp_servers.json"
    cfg_file.write_text(json.dumps([
        {
            "name": "fetch",
            "transport": "sse",
            "url": "http://localhost:3000/sse"
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
            captured['url'] = params.url

        @property
        def tools(self):
            return {}

    monkeypatch.setattr(mcp_manager, 'ClientSessionGroup', lambda: DummyGroup())

    class DummyPortal:
        def call(self, func, *args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                return asyncio.run(func(*args, **kwargs))
            return func(*args, **kwargs)

        def stop(self):
            captured['stopped'] = True

    monkeypatch.setattr(mcp_manager, 'start_blocking_portal', lambda: DummyPortal())
    mcp_manager.stop_mcp_sqlite()

    mcp_manager.start_mcp_sqlite(str(tmp_path / "db.sqlite"))
    assert captured['url'] == "http://localhost:3000/sse"
    mcp_manager.stop_mcp_sqlite()
    monkeypatch.delenv("RETRORECON_MCP_SERVERS_FILE")
