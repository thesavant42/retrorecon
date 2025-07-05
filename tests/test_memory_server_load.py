import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mcp_manager


def test_memory_server_started(monkeypatch, tmp_path):
    cfg_file = tmp_path / "mcp_servers.json"
    cfg_file.write_text(json.dumps([
        {
            "name": "memory",
            "transport": "stdio",
            "command": ["echo", "memory"],
        }
    ]))
    monkeypatch.setenv("RETRORECON_MCP_SERVERS_FILE", str(cfg_file))

    popen_called = {}

    class DummyProc:
        def __init__(self, *args, **kwargs):
            popen_called['cmd'] = args[0]
        def terminate(self):
            pass
        def wait(self, timeout=None):
            pass

    monkeypatch.setattr(mcp_manager.subprocess, 'Popen', lambda *a, **k: DummyProc(*a, **k))
    mcp_manager.stop_mcp_sqlite()

    server = mcp_manager.start_mcp_sqlite(str(tmp_path / "db.sqlite"))
    assert popen_called['cmd'] == ["echo", "memory"]
    mcp_manager.stop_mcp_sqlite()
    monkeypatch.delenv("RETRORECON_MCP_SERVERS_FILE")
