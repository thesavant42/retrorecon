import io
import tarfile
import asyncio
import zstandard as zstd

from layerslayer.client import list_layer_files, DockerRegistryClient

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
            raise Exception('bad')

class FakeSession:
    def __init__(self, first_chunk):
        self.calls = 0
        self.first_chunk = first_chunk
    def get(self, url, headers=None):
        self.calls += 1
        if self.calls == 1:
            return FakeResp(self.first_chunk, 206)
        return FakeResp(b'', 416)

async def run_test(client, tar_bytes):
    client.session = FakeSession(tar_bytes[:10])
    files = await list_layer_files('u/r:tag', 'sha256:x', client)
    return files

def test_zstd_layer_fallback(monkeypatch):
    # create tiny tar and compress with zstd
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode='w') as tar:
        info = tarfile.TarInfo('hi.txt')
        data = b'hi'
        info.size = len(data)
        tar.addfile(info, io.BytesIO(data))
    comp = zstd.ZstdCompressor().compress(buf.getvalue())

    async def fake_fetch_bytes(self, url, user, repo):
        return comp
    async def fake_auth_headers(self, user, repo):
        return {}

    monkeypatch.setattr(DockerRegistryClient, 'fetch_bytes', fake_fetch_bytes)
    monkeypatch.setattr(DockerRegistryClient, '_auth_headers', fake_auth_headers)

    client = DockerRegistryClient()
    files = asyncio.run(run_test(client, comp))
    assert files == ['-rw-r--r-- 0/0 2 1970-01-01 00:00 hi.txt']
