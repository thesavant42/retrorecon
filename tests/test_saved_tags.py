import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    monkeypatch.setattr(app, "SAVED_TAGS_FILE", str(tmp_path / "tags.json"))


def test_saved_tag_crud(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/saved_tags')
        assert resp.get_json() == {"tags": []}

        resp = client.post('/saved_tags', data={'tag': 'foo'})
        assert resp.status_code == 204
        assert (tmp_path / "tags.json").exists()

        resp = client.get('/saved_tags')
        assert resp.get_json() == {"tags": ["#foo"]}

        client.post('/saved_tags', data={'tag': 'foo'})  # duplicate
        resp = client.get('/saved_tags')
        assert resp.get_json() == {"tags": ["#foo"]}

        resp = client.post('/delete_saved_tag', data={'tag': 'foo'})
        assert resp.status_code == 204
        resp = client.get('/saved_tags')
        assert resp.get_json() == {"tags": []}


def test_load_legacy_tags(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    legacy = [
        {"name": ".js", "color": "#181ed8"},
        {"name": ".zip", "color": "#edb10c"}
    ]
    with open(tmp_path / "tags.json", "w") as f:
        json.dump(legacy, f)
    with app.app.test_client() as client:
        resp = client.get('/saved_tags')
        assert resp.get_json() == {"tags": ["#.js", "#.zip"]}
        resp = client.post('/delete_saved_tag', data={'tag': '.js'})
        assert resp.status_code == 204
        resp = client.get('/saved_tags')
        assert resp.get_json() == {"tags": ["#.zip"]}
