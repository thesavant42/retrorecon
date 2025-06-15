import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_adv_db(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    with app.app.app_context():
        app.create_new_db("search")
        app.execute_db(
            "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?)",
            ["http://a.example/file1", "20230101", 200, "text/html", "alpha"],
        )
        app.execute_db(
            "INSERT INTO urls (url, timestamp, status_code, mime_type, tags) VALUES (?, ?, ?, ?, ?)",
            ["http://b.example/file2", "20230202", 404, "text/plain", "beta"],
        )
    return app.app.test_client()


def test_http_status(monkeypatch, tmp_path):
    client = setup_adv_db(monkeypatch, tmp_path)
    resp = client.get("/?q=http:200")
    assert resp.status_code == 200
    assert b"http://a.example/file1" in resp.data
    assert b"http://b.example/file2" not in resp.data


def test_not_http(monkeypatch, tmp_path):
    client = setup_adv_db(monkeypatch, tmp_path)
    resp = client.get("/?q=NOT+http:404")
    assert resp.status_code == 200
    assert b"http://a.example/file1" in resp.data
    assert b"http://b.example/file2" not in resp.data


def test_url_filter(monkeypatch, tmp_path):
    client = setup_adv_db(monkeypatch, tmp_path)
    resp = client.get("/?q=url:b.example")
    assert resp.status_code == 200
    assert b"http://b.example/file2" in resp.data
    assert b"http://a.example/file1" not in resp.data


def test_http_and_mime(monkeypatch, tmp_path):
    client = setup_adv_db(monkeypatch, tmp_path)
    resp = client.get("/?q=http:200+AND+mime:text/html")
    assert resp.status_code == 200
    assert b"http://a.example/file1" in resp.data
    assert b"http://b.example/file2" not in resp.data

