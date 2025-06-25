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
    monkeypatch.setattr(app, "SCREENSHOT_DIR", str(tmp_path / "static" / "screenshots"))
    monkeypatch.setattr(app, "SITEZIP_DIR", str(tmp_path / "static" / "sitezips"))
    with app.app.app_context():
        app.create_new_db("test")


def test_screenshot_route_debug_logs(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)

    def fake_take(url, agent='', spoof=False, log_path=None):
        assert log_path is not None
        assert os.path.isdir(os.path.dirname(log_path))
        return b"IMG", 200, "1.1.1.1"

    monkeypatch.setattr(app, "take_screenshot", fake_take)

    with app.app.test_client() as client:
        resp = client.post(
            "/tools/screenshot",
            data={"url": "http://example.com", "debug": "1"},
        )
        assert resp.status_code == 200


def test_httpolaroid_route_debug_logs(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)

    def fake_capture(url, agent="", spoof=False, log_path=None):
        assert log_path is not None
        assert os.path.isdir(os.path.dirname(log_path))
        return b"ZIP", b"IMG", 200, "1.1.1.1"

    monkeypatch.setattr(app, "capture_snap", fake_capture)

    with app.app.test_client() as client:
        resp = client.post(
            "/tools/httpolaroid",
            data={"url": "http://example.com", "debug": "1"},
        )
        assert resp.status_code == 200
