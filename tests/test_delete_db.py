import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    (tmp_path / "data").mkdir(exist_ok=True)
    (tmp_path / "db").mkdir(exist_ok=True)
    schema = Path(__file__).resolve().parents[1] / "db" / "schema.sql"
    (tmp_path / "db" / "schema.sql").write_text(schema.read_text())
    monkeypatch.setitem(app.app.config, "DATABASE", str(tmp_path / "test.db"))
    with app.app.app_context():
        app.create_new_db("test")


def test_delete_db(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    extra = tmp_path / "db" / "extra.db"
    extra.write_text("x")
    with app.app.test_client() as client:
        resp = client.post("/delete_db", data={"db_file": "extra.db"})
        assert resp.status_code == 204
    assert not extra.exists()


def test_delete_active_db(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    active = tmp_path / "db" / "test.db"
    assert active.exists()
    with app.app.test_client() as client:
        resp = client.post("/delete_db", data={"db_file": "test.db"})
        assert resp.status_code == 400
    assert active.exists()
