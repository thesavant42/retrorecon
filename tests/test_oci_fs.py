import io
import tarfile
import zipfile
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


def make_tar_with_file(name: str, data: bytes) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tar:
        info = tarfile.TarInfo(name)
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def test_fs_text_file(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    from retrorecon.routes import oci

    tar_bytes = make_tar_with_file('a.txt', b'hello')

    async def fake_read(repo, digest):
        return tar_bytes

    monkeypatch.setattr(oci, '_read_layer', fake_read)

    with app.app.test_client() as client:
        resp = client.get('/fs/repo@sha256:x/a.txt')
        assert resp.status_code == 200
        assert resp.data == b'hello'


def test_fs_binary_hex(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    from retrorecon.routes import oci

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w') as z:
        z.writestr('b.txt', 'hi')
    tar_bytes = make_tar_with_file('dist.zip', zip_buf.getvalue())

    async def fake_read(repo, digest):
        return tar_bytes

    monkeypatch.setattr(oci, '_read_layer', fake_read)

    with app.app.test_client() as client:
        resp = client.get('/fs/repo@sha256:x/dist.zip')
        assert resp.status_code == 200
        assert b'00000000:' in resp.data


def test_fs_text_file_no_ext(tmp_path, monkeypatch):
    setup_tmp(monkeypatch, tmp_path)
    from retrorecon.routes import oci

    tar_bytes = make_tar_with_file('.wh..wh..opq', b'')

    async def fake_read(repo, digest):
        return tar_bytes

    monkeypatch.setattr(oci, '_read_layer', fake_read)

    with app.app.test_client() as client:
        resp = client.get('/fs/repo@sha256:x/.wh..wh..opq')
        assert resp.status_code == 200
        assert resp.data == b''
        assert resp.headers['Content-Type'].startswith('text/plain')

