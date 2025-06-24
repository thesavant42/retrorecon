import io
import tarfile
import logging
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


def test_repo_route_domain_only(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci
    import aiohttp

    called = {}

    class FakeResp:
        status = 200

        async def json(self):
            return {"child": ["a"], "tags": [], "manifest": {}}

        def raise_for_status(self):
            pass

    def fake_get(self, url):
        called["url"] = url

        class CM:
            async def __aenter__(self_inner):
                return FakeResp()

            async def __aexit__(self_inner, exc_type, exc, tb):
                pass

        return CM()

    monkeypatch.setattr(aiohttp.ClientSession, "get", fake_get)

    with app.app.test_client() as client:
        resp = client.get("/repo/registry.k8s.io")
        assert resp.status_code == 200
        assert b"registry.k8s.io" in resp.data
        assert called["url"].startswith("https://registry.k8s.io/v2/")


def test_image_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None):
        return {"layers": [{"digest": "sha256:x"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:x"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo:tag")
        assert resp.status_code == 200
        assert b"sha256:x" in resp.data
        assert b'/layers/user/repo:tag@sha256:x/' in resp.data


def test_image_route_no_size_links(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None):
        return {"layers": [{"digest": "sha256:x", "size": 1}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:x"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo:tag")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "/size/user/repo" not in html


def test_image_route_manifest_index(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, specific_digest=None, client=None):
        if specific_digest is None:
            return {"manifests": [{"digest": "sha256:d"}]}
        assert specific_digest == "sha256:d"
        return {"layers": [{"digest": "sha256:x"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:d"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo:tag")
        assert resp.status_code == 200
        assert b'<a href="/image/user/repo@sha256:d">sha256:d</a>' in resp.data


def test_image_route_manifest_annotations(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, specific_digest=None, client=None):
        if specific_digest is None:
            return {"manifests": [{"digest": "sha256:d", "annotations": {"foo": "bar"}}]}
        assert specific_digest == "sha256:d"
        return {"layers": [{"digest": "sha256:x", "annotations": {"hello": "world"}}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:d"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo:tag")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert '"foo": "bar"' in html
        resp = client.get("/image/user/repo@sha256:d")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert '"hello": "world"' in html


def test_image_digest_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, specific_digest=None, client=None):
        assert specific_digest == "sha256:y"
        return {"layers": [{"digest": "sha256:z"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    with app.app.test_client() as client:
        resp = client.get("/image/user/repo@sha256:y")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "sha256:z" in html
        assert "user/repo@sha256:y" in html
        assert "/layers/user/repo@sha256:y/" in html


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


def test_fs_root_listing(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        info = tarfile.TarInfo("dir/file.txt")
        data = b""
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
        info2 = tarfile.TarInfo("top.txt")
        info2.size = 0
        tar.addfile(info2, io.BytesIO(b""))
    tar_bytes = buf.getvalue()

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return tar_bytes

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        resp = client.get("/fs/user/repo@sha256:x")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "dir/" in html
        assert "top.txt" in html
        resp = client.get("/fs/user/repo@sha256:x?q=top")
        html = resp.data.decode()
        assert "top.txt" in html
        assert "dir/" not in html


def test_fs_route_invalid_tar(tmp_path, monkeypatch, caplog):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return b"not a tar"

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        caplog.set_level(logging.WARNING)
        resp = client.get("/fs/user/repo@sha256:x/a.txt")
        assert resp.status_code == 415
        assert b"invalid tar" in resp.data
        assert any("invalid tar for user/repo@sha256:x" in rec.message for rec in caplog.records)


def test_size_route_invalid_tar(tmp_path, monkeypatch, caplog):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return b"not a tar"

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        caplog.set_level(logging.WARNING)
        resp = client.get("/size/user/repo@sha256:x")
        assert resp.status_code == 415
        assert b"invalid tar" in resp.data
        assert any("invalid tar for user/repo@sha256:x" in rec.message for rec in caplog.records)


def test_size_route_unsupported_media(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return b"{}"

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        resp = client.get(
            "/size/user/repo@sha256:x?mt=application/vnd.oci.image.manifest.v1+json"
        )
        assert resp.status_code == 415
        assert b"unsupported media type" in resp.data


def test_layers_overlay_listing(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None, specific_digest=None):
        return {"layers": [{"digest": "sha256:a"}, {"digest": "sha256:b"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:m"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    async def fake_list(image_ref, digest, client=None):
        if digest == "sha256:a":
            return ["-rw-r--r-- 0/0 0 2024-01-01 00:00 foo.txt"]
        return ["-rw-r--r-- 0/0 0 2024-01-01 00:00 bar.txt"]

    monkeypatch.setattr(oci, "list_layer_files", fake_list)

    buf_a = io.BytesIO()
    with tarfile.open(fileobj=buf_a, mode="w") as tar:
        info = tarfile.TarInfo("foo.txt")
        data = b"A"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    data_a = buf_a.getvalue()

    buf_b = io.BytesIO()
    with tarfile.open(fileobj=buf_b, mode="w") as tar:
        info = tarfile.TarInfo("bar.txt")
        data = b"B"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    data_b = buf_b.getvalue()

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return data_a if digest == "sha256:a" else data_b

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        resp = client.get("/layers/user/repo:tag@sha256:m/")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "foo.txt" in html
        assert "bar.txt" in html
        assert '/fs/user/repo@sha256:a' in html
        assert 'href="/layers/user/repo:tag@sha256:m/foo.txt"' in html

        resp = client.get("/layers/user/repo:tag@sha256:m/foo.txt")
        assert resp.status_code == 200
        assert resp.data == b"A"


def test_layers_overlay_alt_manifest(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.oci as oci

    async def fake_manifest(image, client=None, specific_digest=None):
        if specific_digest == "sha256:m1":
            return {"layers": [{"digest": "sha256:a"}]}
        if specific_digest == "sha256:m2":
            return {"layers": [{"digest": "sha256:b"}]}
        return {"manifests": [{"digest": "sha256:m1"}, {"digest": "sha256:m2"}]}

    monkeypatch.setattr(oci, "get_manifest", fake_manifest)

    async def fake_digest(image, client=None):
        return "sha256:index"

    monkeypatch.setattr(oci, "get_manifest_digest", fake_digest)

    async def fake_resolve(image):
        return {"manifests": [{"digest": "sha256:m1"}, {"digest": "sha256:m2"}]}

    monkeypatch.setattr(oci, "_resolve_manifest", fake_resolve)

    async def fake_list(image_ref, digest, client=None):
        if digest == "sha256:a":
            return ["-rw-r--r-- 0/0 0 2024-01-01 00:00 foo.txt"]
        return ["-rw-r--r-- 0/0 0 2024-01-01 00:00 bar.txt"]

    monkeypatch.setattr(oci, "list_layer_files", fake_list)

    buf_a = io.BytesIO()
    with tarfile.open(fileobj=buf_a, mode="w") as tar:
        info = tarfile.TarInfo("foo.txt")
        data = b"A"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    data_a = buf_a.getvalue()

    buf_b = io.BytesIO()
    with tarfile.open(fileobj=buf_b, mode="w") as tar:
        info = tarfile.TarInfo("bar.txt")
        data = b"B"
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    data_b = buf_b.getvalue()

    async def fake_fetch_token(repo):
        return "t"

    async def fake_fetch_blob(repo, digest, token, session=None):
        return data_a if digest == "sha256:a" else data_b

    monkeypatch.setattr(oci, "fetch_token", fake_fetch_token)
    monkeypatch.setattr(oci, "fetch_blob", fake_fetch_blob)

    with app.app.test_client() as client:
        resp = client.get("/layers/user/repo:tag@sha256:m2/")
        assert resp.status_code == 200
        html = resp.data.decode()
        assert "bar.txt" in html
        assert "/fs/user/repo@sha256:b" in html

