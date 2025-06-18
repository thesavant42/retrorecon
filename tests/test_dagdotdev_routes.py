import io
import tarfile
from pathlib import Path
import sys

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


def test_r_repo_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dagdotdev as dd
    import retrorecon.routes.oci as oci

    async def fake_fetch_json(self, url, user, repo):
        return {"tags": ["v1"]}

    async def fake_fetch_digest(self, url, user, repo):
        return "sha256:d"

    monkeypatch.setattr(oci.DockerRegistryClient, "fetch_json", fake_fetch_json)
    monkeypatch.setattr(oci.DockerRegistryClient, "fetch_digest", fake_fetch_digest)

    with app.app.test_client() as client:
        resp = client.get("/r/user/repo")
        assert resp.status_code == 200
        assert b"v1" in resp.data
        assert b"sha256:d" in resp.data


def test_r_image_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dagdotdev as dd
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None):
        return {"layers": [{"digest": "sha256:x"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:x"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/r/user/repo:tag")
        assert resp.status_code == 200
        assert b"sha256:x" in resp.data


def test_fs_alias_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dagdotdev as dd
    import retrorecon.routes.dag as dag

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo("a.txt")
        data = b"hello"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_bytes = buf.getvalue()

    async def fake_fetch_bytes(self, url, user, repo):
        return tar_bytes

    monkeypatch.setattr(dag.DockerRegistryClient, "fetch_bytes", fake_fetch_bytes)

    with app.app.test_client() as client:
        resp = client.get("/fs/sha256:x/a.txt?image=user/repo:tag")
        assert resp.status_code == 200
        assert resp.data == b"hello"


def test_layer_alias_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dagdotdev as dd
    import retrorecon.routes.dag as dag

    async def fake_list(image_ref, digest, client=None):
        assert image_ref == "user/repo:tag"
        assert digest == "sha256:x"
        return ["a.txt", "b.txt"]

    monkeypatch.setattr(dag, "list_layer_files", fake_list)

    with app.app.test_client() as client:
        resp = client.get("/layer/sha256:x?image=user/repo:tag")
        assert resp.status_code == 200
        assert resp.get_json()["files"] == ["a.txt", "b.txt"]


def test_size_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dagdotdev as dd

    async def fake_fetch_bytes(self, url, user, repo):
        return b"abc"

    monkeypatch.setattr(dd.DockerRegistryClient, "fetch_bytes", fake_fetch_bytes)

    with app.app.test_client() as client:
        resp = client.get("/size/sha256:x?image=user/repo:tag")
        assert resp.status_code == 200
        assert resp.get_json()["size"] == 3
