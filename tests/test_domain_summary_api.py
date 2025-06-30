import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from retrorecon import subdomain_utils


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    (tmp_path / "db" / "schema.sql").write_text(schema.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")


def test_domain_summary_json(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        subdomain_utils.insert_records("example.com", ["a.example.com", "b.example.com"], "crtsh")
        subdomain_utils.insert_records("other.com", ["x.other.com"], "crtsh")
    with app.app.test_client() as client:
        resp = client.get("/domain_summary.json")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_domains"] == 2
        assert data["total_hosts"] == 3
        assert any(dom == "a.example.com" for dom, cnt in data["top_subdomains"])
