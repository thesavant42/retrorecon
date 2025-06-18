import requests
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


def test_local_matches_remote(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        local_resp = client.get("/image/ubuntu:latest")
        assert local_resp.status_code == 200
        local_html = local_resp.get_data(as_text=True)

    remote_resp = requests.get("https://oci.dag.dev/?image=ubuntu:latest", timeout=10)
    remote_resp.raise_for_status()
    remote_html = remote_resp.text

    assert 'schemaVersion' in local_html
    assert 'schemaVersion' in remote_html
    assert 'application/vnd.oci.image.index.v1+json' in local_html
    assert 'application/vnd.oci.image.index.v1+json' in remote_html
