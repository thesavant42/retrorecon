import sys
from pathlib import Path

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
        demo = app.jwt.encode({'sub': '1'}, 'secret', algorithm='HS256')
        resp = client.post('/tools/jwt_decode', data={'token': demo})
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload['sub'] == '1'
        resp = client.post('/tools/jwt_encode', data={'payload': payload, 'secret': 'secret'})
        assert resp.status_code == 200
        new_jwt = resp.get_data(as_text=True)
        assert new_jwt


