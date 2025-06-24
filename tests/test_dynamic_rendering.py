import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "schemas").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())
    # copy example schema
    example_schema = orig / "schemas" / "simple.json"
    if example_schema.exists():
        (tmp_path / "schemas" / "simple.json").write_text(example_schema.read_text())


def test_api_render(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        payload = {
            "schema": "simple",
            "data": {"title": "Demo"}
        }
        resp = client.post("/dynamic/api/render", json=payload)
        assert resp.status_code == 200
        assert "<h1>Demo</h1>" in resp.get_data(as_text=True)

