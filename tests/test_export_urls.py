import io
from pathlib import Path
import sys
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
        app.create_new_db('urls')
        id1 = app.execute_db(
            "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?)",
            ['http://a.com', '20200101', 200, 'text/html', 'tag1']
        )
        id2 = app.execute_db(
            "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?)",
            ['http://b.com', '20200102', 404, 'text/html', 'tag2']
        )
    return id1, id2


def test_export_formats(tmp_path, monkeypatch):
    id1, _ = init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get(f'/export_urls?format=txt&id={id1}')
        assert resp.status_code == 200
        assert b'http://a.com' in resp.data
        resp = client.get('/export_urls?format=csv&select_all_matching=true&q=.com')
        text = resp.data.decode()
        assert 'http://a.com' in text and 'http://b.com' in text
        resp = client.get('/export_urls?format=md&id={}'.format(id1))
        assert resp.status_code == 200
        assert b'| http://a.com |' in resp.data
        resp = client.get('/export_urls?id={}&format=json'.format(id1))
        assert resp.is_json
        data = resp.get_json()
        assert data and data[0]['url'] == 'http://a.com'


def test_export_query_filter(tmp_path, monkeypatch):
    init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/export_urls?format=txt&q=b.com&select_all_matching=true')
        text = resp.data.decode()
        assert 'http://b.com' in text
        assert 'http://a.com' not in text
