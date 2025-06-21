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
        assert b'id="subdomonster-select-all"' in resp.data


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


def test_export_and_mark_cdx(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('exp')
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records('example.com', ['a.example.com'], 'crtsh')
    with app.app.test_client() as client:
        resp = client.get('/export_subdomains?domain=example.com&format=csv')
        assert resp.status_code == 200
        assert b'subdomain,domain,source,cdx_indexed' in resp.data
        resp = client.post('/mark_subdomain_cdx', data={'subdomain': 'a.example.com'})
        assert resp.status_code == 204
    with app.app.app_context():
        rows = subdomain_utils.list_subdomains('example.com')
        assert rows[0]['cdx_indexed'] is True


def test_export_filter(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('expfilter')
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records('example.com', ['a.example.com', 'b.example.com'], 'crtsh')
    with app.app.test_client() as client:
        resp = client.get('/export_subdomains?domain=example.com&format=csv&q=a.example')
        assert resp.status_code == 200
        text = resp.data.decode()
        assert 'a.example.com' in text
        assert 'b.example.com' not in text



def test_scrape_subdomains(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('scrape')
        app.execute_db(
            "INSERT INTO urls (url, domain, tags) VALUES (?, ?, '')",
            ['http://a.example.com', 'a.example.com'],
        )
        app.execute_db(
            "INSERT INTO urls (url, domain, tags) VALUES (?, ?, '')",
            ['http://b.test.org', 'b.test.org'],
        )
    with app.app.test_client() as client:
        resp = client.post('/scrape_subdomains')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['inserted'] >= 2
    with app.app.app_context():
        from retrorecon import subdomain_utils
        rows = subdomain_utils.list_subdomains('example.com')
        subs = [r['subdomain'] for r in rows]
        assert 'a.example.com' in subs

def test_list_all_subdomains_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('listall')
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records('example.com', ['a.example.com'], 'scrape', cdx=True)
        subdomain_utils.insert_records('test.org', ['b.test.org'], 'scrape', cdx=True)
    with app.app.test_client() as client:
        resp = client.get('/subdomains')
        assert resp.status_code == 200
        data = resp.get_json()
        subs = {r['subdomain'] for r in data}
        assert subs == {'a.example.com', 'b.test.org'}

def test_delete_subdomain(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('del')
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records('example.com', ['bad.example.com'], 'crtsh')
    with app.app.test_client() as client:
        resp = client.post('/delete_subdomain', data={'domain': 'example.com', 'subdomain': 'bad.example.com'})
        assert resp.status_code == 204
    with app.app.app_context():
        rows = subdomain_utils.list_subdomains('example.com')
        assert rows == []


def test_scrape_uses_url_when_domain_missing(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('scrapeurl')
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, '')", ['http://x.example.com/a'])
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, '')", ['http://y.test.org/b'])
    with app.app.test_client() as client:
        resp = client.post('/scrape_subdomains')
        assert resp.status_code == 200
    with app.app.app_context():
        from retrorecon import subdomain_utils
        all_rows = subdomain_utils.list_all_subdomains()
        subs = {r['subdomain'] for r in all_rows}
        assert {'x.example.com', 'y.test.org'} <= subs


def test_subdomains_route_local_source(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('localsrc')
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, '')", ['http://a.example.com/'])
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, '')", ['http://b.test.org/'])
    with app.app.test_client() as client:
        resp = client.post('/subdomains', data={'source': 'local'})
        assert resp.status_code == 200
        data = resp.get_json()
        subs = {r['subdomain'] for r in data}
        assert {'a.example.com', 'b.test.org'} <= subs


def test_local_scrape_cdx_flag(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('cdxflag')
        app.execute_db(
            "INSERT INTO urls (url, domain, tags) VALUES (?, ?, '')",
            ['http://c.example.com', 'c.example.com'],
        )
    with app.app.test_client() as client:
        resp = client.post('/subdomains', data={'source': 'local'})
        assert resp.status_code == 200
        data = resp.get_json()
        row = next(r for r in data if r['subdomain'] == 'c.example.com')
        assert row['cdx_indexed'] is True


def test_scrape_multitld_and_ip(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('tldip')
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, '')", ['http://a.example.co.uk'])
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, '')", ['http://192.168.1.10/path'])
    with app.app.test_client() as client:
        resp = client.post('/scrape_subdomains')
        assert resp.status_code == 200
    with app.app.app_context():
        from retrorecon import subdomain_utils
        rows = subdomain_utils.list_all_subdomains()
        results = {(r['subdomain'], r['domain']) for r in rows}
        assert ('a.example.co.uk', 'example.co.uk') in results
        assert ('192.168.1.10', '192.168.1.10') in results


def test_subdomain_pagination(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('paginate')
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records('example.com', ['a.example.com', 'b.example.com', 'c.example.com'], 'crtsh')
    with app.app.test_client() as client:
        resp = client.get('/subdomains?domain=example.com&page=2&items=2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['page'] == 2
        assert data['total_pages'] == 2
        assert data['total_count'] == 3
        subs = [r['subdomain'] for r in data['results']]
        assert subs == ['c.example.com']


def test_subdomain_pagination_all(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('paginateall')
        from retrorecon import subdomain_utils
        subdomain_utils.insert_records('example.com', ['a.example.com'], 'scrape', cdx=True)
        subdomain_utils.insert_records('test.org', ['b.test.org', 'c.test.org'], 'scrape', cdx=True)
    with app.app.test_client() as client:
        resp = client.get('/subdomains?page=1&items=2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total_count'] == 3
        assert data['total_pages'] == 2
    assert len(data['results']) == 2


def test_fetch_then_local_scrape(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('fetchlocal')
    sample = [
        ["orig", "t", "200", "text/plain"],
        ["http://a.example.com", "", "200", "text"],
        ["http://2.example.com", "", "200", "text"],
        ["http://3example.com", "", "200", "text"],
        ["http://3.3xample.com", "", "200", "text"],
    ]
    monkeypatch.setattr(app.requests, 'get', lambda *a, **k: FakeResp(sample))
    with app.app.test_client() as client:
        client.post('/fetch_cdx', data={'domain': 'example.com'})
        resp = client.post('/subdomains', data={'source': 'local'})
        assert resp.status_code == 200
        data = resp.get_json()
        subs = {r['subdomain'] for r in data}
        expected = {"a.example.com", "2.example.com", "3example.com", "3.3xample.com"}
        assert expected <= subs

