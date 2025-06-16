import sys
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)


def test_set_items_per_page(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.post('/set_items_per_page', data={'count': '15'})
        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert sess['items_per_page'] == 15


def test_invalid_items(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.post('/set_items_per_page', data={'count': '7'})
        assert resp.status_code == 400

