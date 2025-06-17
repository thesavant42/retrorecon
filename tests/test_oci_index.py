from pathlib import Path
import app


def setup_tmp(monkeypatch, tmp_path):
    monkeypatch.setattr(app.app, "root_path", str(tmp_path))
    monkeypatch.setitem(app.app.config, "DATABASE", None)
    (tmp_path / "db").mkdir()
    (tmp_path / "data").mkdir()
    orig = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(app.app, "template_folder", str(orig / "templates"))
    (tmp_path / "db" / "schema.sql").write_text((orig / "db" / "schema.sql").read_text())


def test_index_repo_redirect(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/?repo=myrepo')
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/repo/myrepo')


def test_index_image_redirect(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/?image=myimg:latest')
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/image/myimg:latest')
