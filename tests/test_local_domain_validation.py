import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from retrorecon import subdomain_utils
from tests.test_subdomonster import setup_tmp


def test_local_allows_single_label(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db('single')
        app.execute_db("INSERT INTO urls (url, domain, tags) VALUES (?, ?, '')", ['http://internal', 'internal'])
    with app.app.test_client() as client:
        resp = client.post('/subdomains', data={'source': 'local', 'domain': 'internal'})
        assert resp.status_code == 200
        data = resp.get_json()
        subs = {r['subdomain'] for r in data}
        assert 'internal' in subs
