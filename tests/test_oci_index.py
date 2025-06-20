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


def test_index_repo_view(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_fetch_json(self, url, user, repo):
        return {"tags": ["v1"]}

    async def fake_fetch_digest(self, url, user, repo):
        return "sha256:d"

    monkeypatch.setattr(oci.DockerRegistryClient, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(oci.DockerRegistryClient, "fetch_digest", fake_fetch_digest)

    with app.app.test_client() as client:
        resp = client.get('/?repo=user/repo')
        assert resp.status_code == 200
        assert b"v1" in resp.data
        assert b"sha256:d" in resp.data


def test_index_image_view(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None):
        return {"layers": [{"digest": "sha256:x"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:x"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get('/?image=user/repo:tag')
        assert resp.status_code == 200
        assert b"sha256:x" in resp.data
