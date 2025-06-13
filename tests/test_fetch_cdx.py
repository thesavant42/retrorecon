import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

class FakeResponse:
    def __init__(self, data):
        self._data = data
    def raise_for_status(self):
        pass
    def json(self):
        return self._data


def test_fetch_cdx_inserts_status(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    monkeypatch.setitem(app.app.config, "DATABASE", str(db_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    app.init_db()

    sample = [
        ["original", "timestamp", "statuscode", "mimetype"],
        ["http://example.com/", "20250101010101", "200", "text/html"]
    ]
    monkeypatch.setattr(app.requests, 'get', lambda *a, **k: FakeResponse(sample))

    client = app.app.test_client()
    client.post('/fetch_cdx', data={'domain': 'example.com'})

    with app.app.app_context():
        rows = app.query_db('SELECT url, timestamp, status_code, mime_type FROM urls')
    assert len(rows) == 1
    row = rows[0]
    assert row['url'] == "http://example.com/"
    assert row['timestamp'] == "20250101010101"
    assert row['status_code'] == 200
    assert row['mime_type'] == "text/html"


def test_fetch_cdx_handles_dash_status(tmp_path, monkeypatch):
    db_path = tmp_path / "dash.db"
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    monkeypatch.setitem(app.app.config, "DATABASE", str(db_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    app.init_db()

    sample = [
        ["original", "timestamp", "statuscode", "mimetype"],
        ["http://dash.com/", "20250101010101", "-", "text/html"]
    ]
    monkeypatch.setattr(app.requests, 'get', lambda *a, **k: FakeResponse(sample))

    client = app.app.test_client()
    client.post('/fetch_cdx', data={'domain': 'dash.com'})

    with app.app.app_context():
        rows = app.query_db('SELECT status_code FROM urls')
    assert rows[0]['status_code'] is None
