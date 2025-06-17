import sys
from pathlib import Path
import asyncio
import io
import tarfile

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


def test_docker_layers_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    sample = [
        {
            "os": "linux",
            "architecture": "amd64",
            "layers": [
                {"digest": "sha256:a", "size": 1, "files": ["f"]}
            ],
        }
    ]
    import retrorecon.routes.docker as docker_mod

    async def fake_gather(img):
        return sample

    async def fake_digest(img):
        return "sha256:d1"

    monkeypatch.setattr(docker_mod, "gather_layers_info", fake_gather)
    monkeypatch.setattr(docker_mod, "get_manifest_digest", fake_digest)
    with app.app.test_client() as client:
        resp = client.get('/docker_layers?image=test/test:latest')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["owner"] == "test"
        assert data["tag"] == "latest"
        assert data["platforms"][0]["layers"][0]["digest"] == "sha256:a"


def test_docker_layers_timeout(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.docker as docker_mod

    async def fail_gather(img):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(docker_mod, "gather_layers_info", fail_gather)
    with app.app.test_client() as client:
        resp = client.get('/docker_layers?image=test/test:latest')
        assert resp.status_code == 504
        assert resp.get_json()['error'] == 'timeout'


def test_download_layer_success(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.docker as docker_mod

    async def fake_fetch_bytes(self, url, user, repo):
        return b'ARCHIVE'

    monkeypatch.setattr(docker_mod.DockerRegistryClient, 'fetch_bytes', fake_fetch_bytes)
    with app.app.test_client() as client:
        resp = client.get('/download_layer?image=test/test:tag&digest=sha256:abc')
        assert resp.status_code == 200
        assert resp.data == b'ARCHIVE'


def test_download_layer_timeout(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.docker as docker_mod

    async def fail_bytes(self, url, user, repo):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(docker_mod.DockerRegistryClient, 'fetch_bytes', fail_bytes)
    with app.app.test_client() as client:
        resp = client.get('/download_layer?image=test/test:tag&digest=sha256:abc')
        assert resp.status_code == 504


def test_list_layer_files_fallback(monkeypatch):
    import retrorecon.docker_layers as dl
    # create a tiny tar.gz archive
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w:gz') as tar:
        info = tarfile.TarInfo('hello.txt')
        data = b'hello'
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_bytes = buf.getvalue()

    async def fake_fetch_bytes(self, url, user, repo):
        return tar_bytes

    async def fake_auth_headers(self, user, repo):
        return {}

    class FakeResp:
        def __init__(self, data, status):
            self._data = data
            self.status = status
            self.headers = {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def read(self):
            return self._data

        def raise_for_status(self):
            if self.status >= 400 and self.status != 416:
                raise Exception('error')

    class FakeSession:
        def __init__(self):
            self.calls = 0

        def get(self, url, headers=None):
            self.calls += 1
            if self.calls == 1:
                return FakeResp(b'invalid', 206)
            return FakeResp(b'', 416)

    monkeypatch.setattr(dl.DockerRegistryClient, 'fetch_bytes', fake_fetch_bytes)
    monkeypatch.setattr(dl.DockerRegistryClient, '_auth_headers', fake_auth_headers)

    async def run():
        client = dl.DockerRegistryClient()
        client.session = FakeSession()
        return await dl.list_layer_files('user/repo:tag', 'sha256:x', client=client)

    files = asyncio.run(run())
    assert files and files[0].endswith('hello.txt')


