import sys
from pathlib import Path
import json

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


def test_jwt_tools_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/jwt_tools')
        assert resp.status_code == 200
        assert b'id="jwt-tool-input"' in resp.data


def test_jwt_decode_encode_roundtrip(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'rt'})
        demo = app.jwt.encode({'sub': '1'}, 'secret', algorithm='HS256')
        resp = client.post('/tools/jwt_decode', data={'token': demo})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['payload']['sub'] == '1'
        resp = client.post('/tools/jwt_encode', data={'payload': data['payload'], 'secret': 'secret'})
        assert resp.status_code == 200
        new_jwt = resp.get_data(as_text=True)
        assert new_jwt


def test_jwt_encode_handles_header_input(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'rt2'})
        token = app.jwt.encode({'iss': 'me'}, 'secret', algorithm='HS256')
        resp = client.post('/tools/jwt_decode', data={'token': token})
        data = resp.get_json()
        text = json.dumps(data['header'], indent=2) + "\n" + json.dumps(data['payload'], indent=2)
        resp2 = client.post('/tools/jwt_encode', data={'payload': text, 'secret': 'secret'})
        assert resp2.status_code == 200
        new_token = resp2.get_data(as_text=True)
        decoded = app.jwt.decode(new_token, 'secret', algorithms=['HS256'])
        assert decoded['iss'] == 'me'


def test_jwt_decode_warnings_and_exp(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'warn'})
        none_token = app.jwt.encode({'sub': '1'}, '', algorithm='none')
        resp = client.post('/tools/jwt_decode', data={'token': none_token})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['alg_warning'] is True

        import datetime
        exp = int((datetime.datetime.utcnow() - datetime.timedelta(seconds=1)).timestamp())
        token = app.jwt.encode({'exp': exp}, 'secret', algorithm='HS256')
        resp = client.post('/tools/jwt_decode', data={'token': token})
        data = resp.get_json()
        assert 'exp_readable' in data
        assert data['expired'] is True
        assert data['key_warning'] is True


def test_jwt_cookie_logging(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post('/new_db', data={'db_name': 'jwtlog'})
        token = app.jwt.encode({'iss': 'me'}, '', algorithm='none')
        resp = client.post('/tools/jwt_decode', data={'token': token})
        assert resp.status_code == 200
        resp = client.get('/jwt_cookies')
        data = resp.get_json()
        assert data and data[0]['issuer'] == 'me'
        assert data[0]['token'] == token


def test_jwt_decode_requires_db(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        token = app.jwt.encode({'sub': 1}, '', algorithm='none')
        resp = client.post('/tools/jwt_decode', data={'token': token})
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error'] == 'no_db'


