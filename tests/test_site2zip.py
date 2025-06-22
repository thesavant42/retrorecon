from pathlib import Path
import app
from retrorecon import sitezip_service


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "static" / "sitezips").mkdir(parents=True)
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


def test_site2zip_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/site2zip')
        assert resp.status_code == 200
        assert b'id="sitezip-overlay"' in resp.data


def test_site2zip_workflow(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('sitezip')
    with app.app.test_client() as client:
        def fake_capture(url, agent, spoof):
            return b'ZIPDATA', b'PNGDATA'
        monkeypatch.setattr(sitezip_service, 'capture_site', fake_capture)
        resp = client.post('/tools/site2zip', data={'url': 'http://example.com'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'id' in data
        sid = data['id']
        resp = client.get('/sitezips')
        rows = resp.get_json()
        assert rows and rows[0]['url'] == 'http://example.com'
        assert 'preview' in rows[0]
        resp = client.post('/delete_sitezips', data={'ids': sid})
        assert resp.status_code == 204
        assert client.get('/sitezips').get_json() == []
