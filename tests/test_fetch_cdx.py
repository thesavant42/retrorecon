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
    with app.app.app_context():
        app.init_db()

    sample = [
        ["original", "timestamp", "statuscode", "mimetype"],
        ["http://example.com/", "20250101010101", "200", "text/html"]
    ]
    monkeypatch.setattr(app.requests, 'get', lambda *a, **k: FakeResponse(sample))

    client = app.app.test_client()
    client.post('/fetch_cdx', data={'domain': 'example.com'})

    with app.app.app_context():
        rows = app.query_db('SELECT url, domain, timestamp, status_code, mime_type FROM urls')
    assert len(rows) == 1
    row = rows[0]
    assert row['url'] == "http://example.com/"
    assert row['domain'] == "example.com"
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
    with app.app.app_context():
        app.init_db()

    sample = [
        ["original", "timestamp", "statuscode", "mimetype"],
        ["http://dash.com/", "20250101010101", "-", "text/html"]
    ]
    monkeypatch.setattr(app.requests, 'get', lambda *a, **k: FakeResponse(sample))

    client = app.app.test_client()
    client.post('/fetch_cdx', data={'domain': 'dash.com'})

    with app.app.app_context():
        rows = app.query_db('SELECT status_code, domain FROM urls')
    assert rows[0]['status_code'] is None
    assert rows[0]['domain'] == "dash.com"


def test_fetch_cdx_rejects_invalid_domain(tmp_path, monkeypatch):
    db_path = tmp_path / "reject.db"
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    monkeypatch.setitem(app.app.config, "DATABASE", str(db_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    with app.app.app_context():
        app.init_db()

    called = False

    def fake_get(*a, **k):
        nonlocal called
        called = True
        return FakeResponse([])

    monkeypatch.setattr(app.requests, 'get', fake_get)

    client = app.app.test_client()
    client.post('/fetch_cdx', data={'domain': 'http://bad'})

    assert not called
    with app.app.app_context():
        rows = app.query_db('SELECT COUNT(*) AS c FROM urls')
    assert rows[0]['c'] == 0


def test_fetch_cdx_uses_limit_param(tmp_path, monkeypatch):
    db_path = tmp_path / "limit.db"
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    monkeypatch.setitem(app.app.config, "DATABASE", str(db_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    with app.app.app_context():
        app.init_db()

    captured = None

    def fake_get(url, *a, **k):
        nonlocal captured
        captured = url
        return FakeResponse([["o", "t", "200", "text/plain"]])

    monkeypatch.setattr(app.requests, "get", fake_get)

    client = app.app.test_client()
    client.post('/fetch_cdx', data={'domain': 'limit.com'})

    assert 'limit=1000' in captured
