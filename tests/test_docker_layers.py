import sys
from pathlib import Path
import asyncio

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

    monkeypatch.setattr(docker_mod, "gather_layers_info", fake_gather)
    with app.app.test_client() as client:
        resp = client.get('/docker_layers?image=test/test:latest')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data[0]["layers"][0]["digest"] == "sha256:a"


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


