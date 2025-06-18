import sys
from pathlib import Path
import io
import tarfile
import logging

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


def test_dag_explorer_page(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    with app.app.test_client() as client:
        resp = client.get('/dag_explorer')
        assert resp.status_code == 200
        assert b'id="dag-explorer-overlay"' in resp.data




def test_dag_repo_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dag as dag

    async def fake_fetch_json(self, url, user, repo):
        return {"name": f"{user}/{repo}", "tags": ["latest"]}

    monkeypatch.setattr(dag.DockerRegistryClient, 'fetch_json', fake_fetch_json)
    with app.app.test_client() as client:
        resp = client.get('/dag/repo/user/repo')
        assert resp.status_code == 200
        assert resp.get_json()['tags'] == ['latest']


def test_dag_image_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dag as dag

    async def fake_manifest(image, client=None):
        return {"schemaVersion": 2}

    monkeypatch.setattr(dag, 'get_manifest', fake_manifest)
    with app.app.test_client() as client:
        resp = client.get('/dag/image/user/repo:tag')
        assert resp.status_code == 200
        assert resp.get_json()['schemaVersion'] == 2


def test_dag_fs_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dag as dag

    # create small tar
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tar:
        info = tarfile.TarInfo('a.txt')
        data = b'hello'
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    tar_bytes = buf.getvalue()

    async def fake_fetch_bytes(self, url, user, repo):
        return tar_bytes

    monkeypatch.setattr(dag.DockerRegistryClient, 'fetch_bytes', fake_fetch_bytes)
    with app.app.test_client() as client:
        resp = client.get('/dag/fs/sha256:x/a.txt?image=user/repo:tag')
        assert resp.status_code == 200
        assert resp.data == b'hello'


def test_dag_fs_invalid_tar(tmp_path, monkeypatch, caplog):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dag as dag

    async def fake_fetch_bytes(self, url, user, repo):
        return b"invalid"

    monkeypatch.setattr(dag.DockerRegistryClient, 'fetch_bytes', fake_fetch_bytes)
    with app.app.test_client() as client:
        caplog.set_level(logging.WARNING)
        resp = client.get('/dag/fs/sha256:x/a.txt?image=user/repo:tag')
        assert resp.status_code == 415
        assert resp.get_json()['error'] == 'invalid_blob'
        assert any('invalid tar blob' in rec.message for rec in caplog.records)


def test_dag_layer_route(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    import retrorecon.routes.dag as dag

    async def fake_list(image_ref, digest, client=None):
        assert image_ref == 'user/repo:tag'
        assert digest == 'sha256:x'
        return ['a.txt', 'b.txt']

    monkeypatch.setattr(dag, 'list_layer_files', fake_list)

    with app.app.test_client() as client:
        resp = client.get('/dag/layer/sha256:x?image=user/repo:tag')
        assert resp.status_code == 200
        assert resp.get_json()['files'] == ['a.txt', 'b.txt']
