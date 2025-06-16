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


class FakeResp:
    def __init__(self, data):
        self._data = data
    def raise_for_status(self):
        pass
    def json(self):
        return self._data


def test_subdomonster_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/subdomonster')
        assert resp.status_code == 200
        assert b'id="subdomonster-overlay"' in resp.data


def test_subdomain_insert(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('subs')
    sample = [
        {
            "common_name": "*.skip.example.com",
            "name_value": "a.example.com\\nb.example.com",
        },
        {
            "common_name": "c.example.com",
            "name_value": "c.example.com\\nd.example.com",
        },
    ]
    monkeypatch.setattr(app.requests, 'get', lambda *a, **k: FakeResp(sample))
    with app.app.test_client() as client:
        resp = client.post('/subdomains', data={'domain': 'example.com'})
        assert resp.status_code == 200
        data = resp.get_json()
        subs = [r['subdomain'] for r in data]
        assert set(subs) == {
            'a.example.com',
            'b.example.com',
            'c.example.com',
            'd.example.com',
        }
        assert all(r['domain'] == 'example.com' for r in data)
        assert all('*' not in s for s in subs)


def test_subdomain_invalid_domain(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    called = False
    def fake_get(*a, **k):
        nonlocal called
        called = True
        return FakeResp([])
    monkeypatch.setattr(app.requests, 'get', fake_get)
    with app.app.test_client() as client:
        resp = client.post('/subdomains', data={'domain': 'http://bad'})
        assert resp.status_code == 400
    assert not called


def test_subdomain_virustotal(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('vt')
    samples = [
        {"data": [{"id": "a.example.com"}], "links": {"next": "n"}},
        {"data": [{"id": "b.example.com"}], "links": {}}
    ]
    idx = 0
    def fake_get(url, *a, **k):
        nonlocal idx
        resp = FakeResp(samples[idx])
        idx += 1
        return resp
    monkeypatch.setattr(app.requests, 'get', fake_get)
    with app.app.test_client() as client:
        resp = client.post('/subdomains', data={'domain': 'example.com', 'source': 'virustotal', 'api_key': 'k'})
        assert resp.status_code == 200
        data = resp.get_json()
        subs = [r['subdomain'] for r in data]
        assert set(subs) == {'a.example.com', 'b.example.com'}
        assert all(r['source'] == 'virustotal' for r in data)

