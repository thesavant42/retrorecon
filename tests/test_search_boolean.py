import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_search_db(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    with app.app.app_context():
        app.create_new_db("search")
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://a.example/", "hostA,blue,tag1"])
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://b.example/", "hostB,red,tag1"])
    return app.app.test_client()

def setup_space_tag_db(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    with app.app.app_context():
        app.create_new_db("search")
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://a.example/", "tag1,tag 2"])
        app.execute_db("INSERT INTO urls (url, tags) VALUES (?, ?)", ["http://b.example/", "tag1,tag4"])
    return app.app.test_client()


def test_tag_and(monkeypatch, tmp_path):
    client = setup_search_db(monkeypatch, tmp_path)
    resp = client.get("/?q=%23tag1+AND+%23red")
    assert resp.status_code == 200
    assert b"http://b.example/" in resp.data
    assert b"http://a.example/" not in resp.data


def test_tag_not(monkeypatch, tmp_path):
    client = setup_search_db(monkeypatch, tmp_path)
    resp = client.get("/?q=NOT+%23hostB")
    assert resp.status_code == 200
    assert b"http://a.example/" in resp.data
    assert b"http://b.example/" not in resp.data


def test_tag_with_space(monkeypatch, tmp_path):
    client = setup_space_tag_db(monkeypatch, tmp_path)
    resp = client.get("/?q=%23tag%202%20AND%20NOT%20%23tag4")
    assert resp.status_code == 200
    assert b"http://a.example/" in resp.data
    assert b"http://b.example/" not in resp.data
    resp = client.get("/?q=%23%22tag%202%22")
    assert resp.status_code == 200
    assert b"http://a.example/" in resp.data
