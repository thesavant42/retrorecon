import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "one.md").write_text("hello")
    monkeypatch.setitem(app.app.config, "MARKDOWN_STORAGE", str(docs))


def test_markdown_file_routes(monkeypatch, tmp_path):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get("/markdown_files")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "one.md" in data
        resp = client.get("/markdown_file/one.md")
        assert resp.status_code == 200
        assert resp.get_data(as_text=True) == "hello"
