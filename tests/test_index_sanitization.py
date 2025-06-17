import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


def test_no_inline_url_js(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db("test")
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://a.com", ""])
    with app.app.test_client() as client:
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'onclick="window.open' not in html
        assert 'onchange="handleToolSelect' not in html
        assert 'data-url="http://a.com"' in html

