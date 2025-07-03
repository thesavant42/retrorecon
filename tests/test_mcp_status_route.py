import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    (tmp_path / "db" / "schema.sql").write_text(schema.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")
    if hasattr(app, "mcp_server"):
        delattr(app, "mcp_server")


def test_mcp_status_ok(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get("/chat/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is True
        assert "db" in data


def test_mcp_status_failure(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    if hasattr(app, "mcp_server"):
        delattr(app, "mcp_server")
    with app.app.test_client() as client:
        resp = client.get("/chat/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["ok"] is False
        assert "error" in data
