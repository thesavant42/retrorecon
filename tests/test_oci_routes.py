import io
import tarfile
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


def test_repo_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_fetch_json(self, url, user, repo):
        return {"tags": ["v1"]}

    async def fake_fetch_digest(self, url, user, repo):
        return "sha256:d"

    monkeypatch.setattr(oci.DockerRegistryClient, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(oci.DockerRegistryClient, "fetch_digest", fake_fetch_digest)

    with app.app.test_client() as client:
        resp = client.get("/repo/user/repo")
        assert resp.status_code == 200
        assert b"v1" in resp.data
        assert b"sha256:d" in resp.data


def test_image_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None):
        return {"layers": [{"digest": "sha256:x"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo:tag")
        assert resp.status_code == 200
        assert b"sha256:x" in resp.data


def test_image_route_manifest_index(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, specific_digest=None, client=None):
        if specific_digest is None:
            return {"manifests": [{"digest": "sha256:d"}]}
        assert specific_digest == "sha256:d"
        return {"layers": [{"digest": "sha256:x"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo:tag")
        assert resp.status_code == 200
        assert b'<a href="/?image=user/repo@sha256:d">sha256:d</a>' in resp.data


def test_fs_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo("a.txt")
        data = b"hi"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_bytes = buf.getvalue()

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return tar_bytes

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        resp = client.get("/fs/user/repo@sha256:x/a.txt")
        assert resp.status_code == 200
        assert resp.data == b"hi"

