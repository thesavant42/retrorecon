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


def init_sample(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db("test")
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://a.com", ""])
        url_id = app.query_db("SELECT id FROM urls", one=True)["id"]
    return url_id


def test_add_and_get_note(tmp_path, monkeypatch):
    url_id = init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.post("/notes", data={"url_id": url_id, "content": "Test"})
        assert resp.status_code == 204
        data = client.get(f"/notes/{url_id}").get_json()
        assert len(data) == 1
        assert data[0]["content"] == "Test"


def test_update_note(tmp_path, monkeypatch):
    url_id = init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post("/notes", data={"url_id": url_id, "content": "Test"})
        note_id = client.get(f"/notes/{url_id}").get_json()[0]["id"]
        client.post("/notes", data={"url_id": url_id, "note_id": note_id, "content": "Updated"})
        data = client.get(f"/notes/{url_id}").get_json()
        assert data[0]["content"] == "Updated"


def test_delete_note(tmp_path, monkeypatch):
    url_id = init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post("/notes", data={"url_id": url_id, "content": "Test"})
        note_id = client.get(f"/notes/{url_id}").get_json()[0]["id"]
        client.post("/delete_note", data={"note_id": note_id})
        data = client.get(f"/notes/{url_id}").get_json()
        assert data == []


def test_delete_all_notes(tmp_path, monkeypatch):
    url_id = init_sample(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        client.post("/notes", data={"url_id": url_id, "content": "A"})
        client.post("/notes", data={"url_id": url_id, "content": "B"})
        client.post("/delete_note", data={"url_id": url_id, "all": "1"})
        data = client.get(f"/notes/{url_id}").get_json()
        assert data == []


def test_export_notes(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db("test")
        id1 = app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://a.com", ""])
        id2 = app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://b.com", ""])
    with app.app.test_client() as client:
        client.post("/notes", data={"url_id": id1, "content": "foo"})
        client.post("/notes", data={"url_id": id2, "content": "bar"})
        data = client.get("/export_notes").get_json()
        assert any(item["url"] == "http://a.com" and "foo" in item["notes"] for item in data)
        assert any(item["url"] == "http://b.com" and "bar" in item["notes"] for item in data)
