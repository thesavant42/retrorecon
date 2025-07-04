from retrorecon.mcp.server import RetroReconMCPServer
from retrorecon.mcp.config import load_config


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
