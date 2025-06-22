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


def init_sample(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db("proj")
        app.execute_db("INSERT INTO urls (url, domain, tags) VALUES (?, ?, '')", ["http://a.example/", "a.example"])
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records("example.com", ["a.example"], "crtsh")


def test_overview_page(tmp_path, monkeypatch):
    init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/overview')
        assert resp.status_code == 200
        assert b'example.com' in resp.data


def test_overview_json(tmp_path, monkeypatch):
    init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        data = client.get('/overview.json').get_json()
        assert data['counts']['urls'] == 1
        assert data['counts']['domains'] == 1
