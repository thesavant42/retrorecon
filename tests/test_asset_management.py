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


def test_asset_injection(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.app_context():
        app.create_new_db("assets")
        from retrorecon import asset_utils
        asset_utils.add_asset("/foo.css", "css", 1)
        asset_utils.add_asset("/bar.js", "js", 2)
    with app.app.test_client() as client:
        payload = {"schema": "simple", "data": {"title": "Demo"}}
        from retrorecon.routes.dynamic import schema_registry, asset_registry
        schema_registry.register("simple", {"required": ["title"], "content": [{"tag": "h1", "text": "title"}]})
        asset_registry.loaded = False
        resp = client.post("/dynamic/api/render", json=payload)
        html = resp.get_data(as_text=True)
        assert resp.status_code == 200
        assert '/foo.css' in html
        assert '<script src="/bar.js"' in html

