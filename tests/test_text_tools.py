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


def test_text_tools_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/text_tools')
        assert resp.status_code == 200
        assert b'id="text-tools-overlay"' in resp.data


def test_url_encode_decode_roundtrip(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        original = 'This is a sketchy string!?"'
        resp = client.post('/tools/url_encode', data={'text': original})
        assert resp.status_code == 200
        encoded = resp.get_data(as_text=True)
        resp = client.post('/tools/url_decode', data={'text': encoded})
        assert resp.status_code == 200
        assert resp.get_data(as_text=True) == original


def test_base64_roundtrip(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        text = 'line1\r\nline2\nline3\rend'
        resp = client.post('/tools/base64_encode', data={'text': text})
        assert resp.status_code == 200
        b64 = resp.get_data(as_text=True)
        resp = client.post('/tools/base64_decode', data={'text': b64})
        assert resp.status_code == 200
        assert resp.get_data(as_text=True) == text
