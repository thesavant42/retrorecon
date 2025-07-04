from retrorecon.mcp.server import RetroReconMCPServer
from retrorecon.mcp.config import load_config
from mcp.types import TextContent


def test_answer_question_non_sql(tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    server = RetroReconMCPServer(config=cfg)
    resp = server.answer_question("hello")
    assert isinstance(resp, dict)
    assert "message" in resp


def test_answer_question_sql_rejected(tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    server = RetroReconMCPServer(config=cfg)
    resp = server.answer_question("SELECT 1")
    assert resp.get("error") == "Direct SQL input is not supported in chat"


def test_help_message(tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    server = RetroReconMCPServer(config=cfg)
    resp = server.answer_question("help")
    assert "RetroRecon chat is ready" in resp.get("message", "")
    assert cfg.model in resp.get("message", "")


def test_llm_request(monkeypatch, tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    cfg.api_base = "http://llm"
    cfg.api_key = "key"
    with open(cfg.db_path, "wb"):
        pass

    captured = {}

    def fake_post(url, json, headers, timeout):
        captured["url"] = url
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        class Resp:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {"choices": [{"message": {"content": "hi there"}}]}
        return Resp()

    monkeypatch.setattr("httpx.post", fake_post)

    server = RetroReconMCPServer(config=cfg)
    resp = server.answer_question("What tables exist?")
    assert resp.get("message") == "hi there"
    assert captured["url"] == "http://llm/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer key"
    assert captured["timeout"] == cfg.timeout


def test_time_fallback(monkeypatch, tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    server = RetroReconMCPServer(config=cfg)

    def fake_call(name, args):
        raise Exception("Unknown time zone")

    monkeypatch.setattr(server.server, "_call_tool", fake_call)

    resp = server._call_tool("time_now", {"timezone": "Pacific Standard Time"})
    assert resp["type"] == "text"
    assert "UTC" in resp["text"] or "P" in resp["text"]


def test_windows_timezone_mapping(monkeypatch, tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    with open(cfg.db_path, "wb"):
        pass
    server = RetroReconMCPServer(config=cfg)

    captured = {}

    class FakeResult:
        structured_content = None
        content = [TextContent(type="text", text="hello")]

    def fake_call(name, args):
        captured["tz"] = args.get("timezone")
        return FakeResult()

    monkeypatch.setattr(server.server, "_call_tool", fake_call)

    resp = server._call_tool("time_now", {"timezone": "Pacific Standard Time"})
    assert captured["tz"] == "America/Los_Angeles"
    assert resp["type"] == "text"


def test_multiple_tool_calls(monkeypatch, tmp_path):
    cfg = load_config()
    cfg.db_path = str(tmp_path / "empty.db")
    cfg.api_base = "http://llm"
    with open(cfg.db_path, "wb"):
        pass

    call_count = 0

    def fake_post(url, json, headers, timeout):
        nonlocal call_count
        call_count += 1

        class Resp:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                if call_count == 1:
                    return {
                        "choices": [
                            {"message": {"content": None, "tool_calls": [{"id": "1", "function": {"name": "first", "arguments": "{}"}}]}}
                        ]
                    }
                elif call_count == 2:
                    return {
                        "choices": [
                            {"message": {"content": None, "tool_calls": [{"id": "2", "function": {"name": "second", "arguments": "{}"}}]}}
                        ]
                    }
                else:
                    return {"choices": [{"message": {"content": "done"}}]}

        return Resp()

    monkeypatch.setattr("httpx.post", fake_post)

    server = RetroReconMCPServer(config=cfg)

    calls = []

    def fake_tool(name, args):
        calls.append(name)
        return {"type": "text", "text": name}

    monkeypatch.setattr(server, "_call_tool", fake_tool)

    resp = server.answer_question("multi")
    assert resp["message"] == "done"
    assert calls == ["first", "second"]
    assert len(resp["tools"]) == 2
