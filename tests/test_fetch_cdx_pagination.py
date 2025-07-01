import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


class FakeResp:
    def __init__(self, data):
        self._data = data
        self.status_code = 200

    def raise_for_status(self):
        pass

    def json(self):
        return self._data

    @property
    def text(self):
        return json.dumps(self._data)


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    (tmp_path / "db" / "schema.sql").write_text(schema.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")


def test_fetch_cdx_pagination(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    page1 = [["original", "timestamp", "statuscode", "mimetype"],
             ["http://a.example.com/", "202101", "200", "text/html"],
             ["key123"]]
    page2 = [["original", "timestamp", "statuscode", "mimetype"],
             ["http://b.example.com/", "202102", "200", "text/html"]]

    calls = []

    def fake_get(url, timeout=20):
        calls.append(url)
        if "resumeKey=key123" in url:
            return FakeResp(page2)
        return FakeResp(page1)

    monkeypatch.setattr(app.requests, "get", fake_get)

    with app.app.test_client() as client:
        resp = client.post("/fetch_cdx", data={"domain": "example.com"})
        assert resp.status_code == 302

    with app.app.app_context():
        rows = app.query_db("SELECT url FROM urls ORDER BY id")
        urls = [r["url"] for r in rows]

    assert urls == ["http://a.example.com/", "http://b.example.com/"]
    assert len(calls) == 2
