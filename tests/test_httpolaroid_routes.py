import os
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


def test_httpolaroid_capture(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    def fake_capture(url, agent="", spoof_referrer=False, log_path=None):
        if log_path:
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            Path(log_path).write_text("test log")
        return b"ZIP", b"IMG", 200, "1.1.1.1"
    monkeypatch.setattr(app, "capture_snap", fake_capture)
    import retrorecon.routes.tools as tools_routes
    monkeypatch.setattr(tools_routes, "dynamic_template", lambda *a, **k: "")
    with app.app.test_client() as client:
        resp = client.get("/httpolaroid")
        assert resp.status_code == 200
        resp = client.post("/tools/httpolaroid", data={"url": "http://example.com", "debug": "1"})
        assert resp.status_code == 200
        data = resp.get_json()
        assert isinstance(data.get("id"), int)
        assert data.get("log") == "test log"
        resp = client.get("/httpolaroids")
        assert resp.status_code == 200


def test_httpolaroid_capture_har(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    monkeypatch.setattr(app, "capture_snap", lambda *a, **k: (b"ZIP", b"IMG", 200, "1.1.1.1"))
    import retrorecon.routes.tools as tools_routes
    monkeypatch.setattr(tools_routes, "dynamic_template", lambda *a, **k: "")
    with app.app.test_client() as client:
        resp = client.post("/tools/httpolaroid", data={"url": "http://example.com", "har": "1"})
        assert resp.status_code == 200
        sid = resp.get_json().get("id")
        resp = client.get(f"/download_httpolaroid_har/{sid}")
        assert resp.status_code in (200, 404)


