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


class FakeResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._data


def test_fetch_cdx_accepts_wildcard(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)

    sample = [["original", "timestamp"], ["http://foo.example.com/", "202001"]]
    monkeypatch.setattr(app.requests, "get", lambda url, timeout=20: FakeResp(sample))

    with app.app.test_client() as client:
        resp = client.post("/fetch_cdx", data={"domain": "*.example.com", "ajax": "1"})
        assert resp.status_code == 200
        assert resp.get_json()["inserted"] == 1

    with app.app.app_context():
        row = app.query_db("SELECT url FROM urls", one=True)
        assert row["url"] == "http://foo.example.com/"
