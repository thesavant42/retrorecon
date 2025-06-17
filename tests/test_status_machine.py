import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from retrorecon import status


def test_status_queue_order():
    while status.pop_status() is not None:
        pass
    status.push_status('a', 'first')
    status.push_status('b', 'second')
    assert status.pop_status() == ('a', 'first')
    assert status.pop_status() == ('b', 'second')
    assert status.pop_status() is None


def test_status_route_clears_queue(tmp_path, monkeypatch):
    while status.pop_status() is not None:
        pass
    monkeypatch.setattr(app.app, 'root_path', str(tmp_path))
    monkeypatch.setitem(app.app.config, 'DATABASE', None)
    (tmp_path / 'db').mkdir()
    (tmp_path / 'db' / 'schema.sql').write_text((Path(__file__).resolve().parents[1] / 'db' / 'schema.sql').read_text())
    status.push_status('code1', 'msg1')
    status.push_status('code2', 'msg2')
    with app.app.test_client() as client:
        resp = client.get('/status')
        assert resp.get_json() == {'code': 'code2', 'message': 'msg2'}
    assert status.pop_status() is None


def test_status_route_returns_204_when_empty(tmp_path, monkeypatch):
    while status.pop_status() is not None:
        pass
    monkeypatch.setattr(app.app, 'root_path', str(tmp_path))
    monkeypatch.setitem(app.app.config, 'DATABASE', None)
    (tmp_path / 'db').mkdir()
    (tmp_path / 'db' / 'schema.sql').write_text((Path(__file__).resolve().parents[1] / 'db' / 'schema.sql').read_text())
    with app.app.test_client() as client:
        resp = client.get('/status')
        assert resp.status_code == 204
