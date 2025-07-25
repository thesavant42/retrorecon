import asyncio
import io
import tarfile
import stat
from typing import Any, Dict, List, Optional
import os

import aiohttp

from .utils import parse_image_ref, registry_base_url, human_readable_size

# Python 3.10 compatibility for UTC timezone
try:
    from datetime import datetime, UTC
except ImportError:
    # Fallback for Python 3.10 and earlier
    from datetime import datetime, timezone
    UTC = timezone.utc

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(
    total=int(os.environ.get("REGISTRY_TIMEOUT", "120"))
)


class DockerRegistryClient:
    """Async Docker registry client with simple token caching.

    Parameters
    ----------
    insecure : bool, optional
        If ``True`` disable TLS certificate validation when connecting to
        registries.
    """

    def __init__(self, *, insecure: bool = False) -> None:
        self.session: Optional[aiohttp.ClientSession] = None
        self.token_cache: Dict[str, str] = {}
        self.insecure = insecure

    def _new_session(self) -> aiohttp.ClientSession:
        if self.insecure:
            connector = aiohttp.TCPConnector(ssl=False)
            return aiohttp.ClientSession(
                timeout=DEFAULT_TIMEOUT, connector=connector, trust_env=True
            )
        return aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT, trust_env=True)

    async def __aenter__(self) -> "DockerRegistryClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def _fetch_token(self, user: str, repo: str) -> Optional[str]:
        auth_url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{user}/{repo}:pull"
        async with self._new_session() as sess:
            async with sess.get(auth_url) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                token = data.get("token")
                if token:
                    self.token_cache[f"{user}/{repo}"] = token
                return token

    async def _auth_headers(self, user: str, repo: str) -> Dict[str, str]:
        token = self.token_cache.get(f"{user}/{repo}")
        if not token:
            token = await self._fetch_token(user, repo)
        from .utils import guess_manifest_media_type

        accept = guess_manifest_media_type(user)
        headers = {"Accept": accept}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def fetch_json(self, url: str, user: str, repo: str) -> Dict[str, Any]:
        headers = await self._auth_headers(user, repo)
        if self.session is None:
            self.session = self._new_session()
        async with self.session.get(url, headers=headers) as resp:
            if resp.status == 401:
                token = await self._fetch_token(user, repo)
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    async with self.session.get(url, headers=headers) as resp2:
                        resp2.raise_for_status()
                        return await resp2.json()
            resp.raise_for_status()
            return await resp.json()

    async def fetch_bytes(self, url: str, user: str, repo: str) -> bytes:
        headers = await self._auth_headers(user, repo)
        headers["Accept"] = "*/*"
        if self.session is None:
            self.session = self._new_session()
        async with self.session.get(url, headers=headers) as resp:
            if resp.status == 401:
                token = await self._fetch_token(user, repo)
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    async with self.session.get(url, headers=headers) as resp2:
                        resp2.raise_for_status()
                        return await resp2.read()
            resp.raise_for_status()
            return await resp.read()

    async def fetch_digest(self, url: str, user: str, repo: str) -> Optional[str]:
        headers = await self._auth_headers(user, repo)
        if self.session is None:
            self.session = self._new_session()
        async with self.session.head(url, headers=headers) as resp:
            if resp.status == 401:
                token = await self._fetch_token(user, repo)
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    async with self.session.head(url, headers=headers) as resp2:
                        resp2.raise_for_status()
                        return resp2.headers.get("Docker-Content-Digest")
            resp.raise_for_status()
            return resp.headers.get("Docker-Content-Digest")


def get_client(*, insecure: bool = False) -> DockerRegistryClient:
    """Return a fresh :class:`DockerRegistryClient` instance."""
    return DockerRegistryClient(insecure=insecure)


async def get_manifest_digest(
    image_ref: str,
    client: Optional[DockerRegistryClient] = None,
    *,
    insecure: bool = False,
) -> Optional[str]:
    user, repo, tag = parse_image_ref(image_ref)
    url = f"{registry_base_url(user, repo)}/manifests/{tag}"
    if client is not None:
        return await client.fetch_digest(url, user, repo)
    async with DockerRegistryClient(insecure=insecure) as c:
        return await c.fetch_digest(url, user, repo)


async def get_manifest(
    image_ref: str,
    specific_digest: Optional[str] = None,
    client: Optional[DockerRegistryClient] = None,
    *,
    insecure: bool = False,
) -> Dict[str, Any]:
    user, repo, tag = parse_image_ref(image_ref)
    ref = specific_digest or tag
    url = f"{registry_base_url(user, repo)}/manifests/{ref}"
    if client is not None:
        return await client.fetch_json(url, user, repo)
    async with DockerRegistryClient(insecure=insecure) as c:
        return await c.fetch_json(url, user, repo)


async def list_layer_files(
    image_ref: str,
    digest: str,
    client: Optional[DockerRegistryClient] = None,
    *,
    insecure: bool = False,
) -> List[str]:
    """Return formatted file listing for the layer blob."""
    user, repo, _ = parse_image_ref(image_ref)
    url = f"{registry_base_url(user, repo)}/blobs/{digest}"
    own_client = client is None
    c = client or DockerRegistryClient(insecure=insecure)

    headers = await c._auth_headers(user, repo)
    headers["Accept"] = "*/*"
    if c.session is None:
        c.session = c._new_session()

    range_size = int(os.environ.get("LAYERPEEK_RANGE", "2097152"))

    def _parse(data: bytes) -> List[str]:
        if data.startswith(b"\x28\xb5\x2f\xfd"):
            try:
                import zstandard as zstd  # type: ignore
            except Exception as exc:  # pragma: no cover - optional dep missing
                raise tarfile.ReadError(f"zstd unsupported: {exc}")
            data = zstd.ZstdDecompressor().decompress(data)

        tar_bytes = io.BytesIO(data)
        with tarfile.open(fileobj=tar_bytes, mode="r:*") as tar:
            items = []
            for m in tar.getmembers():
                mode = m.mode
                if m.isfile():
                    mode |= stat.S_IFREG
                elif m.isdir():
                    mode |= stat.S_IFDIR
                elif m.issym():
                    mode |= stat.S_IFLNK
                perms = stat.filemode(mode)
                ts = datetime.fromtimestamp(m.mtime, UTC).strftime("%Y-%m-%d %H:%M")
                items.append(f"{perms} {m.uid}/{m.gid} {m.size} {ts} {m.name}")
            return items

    if range_size <= 0:
        data = await c.fetch_bytes(url, user, repo)
        return _parse(data)

    lookback = 32768
    start = 0
    data = bytearray()
    while True:
        h = dict(headers)
        h["Range"] = f"bytes={start}-{start + range_size - 1}"
        async with c.session.get(url, headers=h) as resp:
            if resp.status == 401:
                token = await c._fetch_token(user, repo)
                if token:
                    h["Authorization"] = f"Bearer {token}"
                    async with c.session.get(url, headers=h) as resp2:
                        if resp2.status == 416:
                            break
                        resp2.raise_for_status()
                        chunk = await resp2.read()
                else:
                    resp.raise_for_status()
                    chunk = await resp.read()
            else:
                if resp.status == 416:
                    break
                resp.raise_for_status()
                chunk = await resp.read()
            if not chunk:
                break
            data.extend(chunk)
            if start == 0 and data.startswith(b"\x28\xb5\x2f\xfd"):
                data = await c.fetch_bytes(url, user, repo)
                return _parse(data)
        try:
            return _parse(data)
        except (tarfile.TarError, OSError, EOFError):
            if len(chunk) < range_size:
                break
            if len(data) > lookback:
                start = len(data) - lookback
                data = data[-lookback:]
            else:
                start = len(data)
            continue
    try:
        return _parse(data)
    except (tarfile.TarError, OSError, EOFError):
        try:
            data = await c.fetch_bytes(url, user, repo)
            return _parse(data)
        except Exception:
            return []
    finally:
        if own_client:
            await c.close()


async def _layers_details(
    image_ref: str,
    manifest: Dict[str, Any],
    client: DockerRegistryClient,
    *,
    insecure: bool = False,
) -> List[Dict[str, Any]]:
    layers = manifest.get("layers", [])
    details: List[Dict[str, Any]] = []
    for layer in layers:
        try:
            files = await list_layer_files(
                image_ref, layer["digest"], client, insecure=insecure
            )
        except Exception:
            files = []
        details.append(
            {
                "digest": layer["digest"],
                "size": human_readable_size(layer.get("size", 0) or 0),
                "files": files,
            }
        )
    return details


async def gather_layers_info(
    image_ref: str,
    *,
    insecure: bool = False,
) -> List[Dict[str, Any]]:
    async with DockerRegistryClient(insecure=insecure) as client:
        manifest_index = await get_manifest(image_ref, client=client, insecure=insecure)
        result: List[Dict[str, Any]] = []
        if manifest_index.get("manifests"):
            platforms = manifest_index["manifests"]
            for m in platforms:
                plat = m.get("platform", {})
                digest = m["digest"]
                manifest = await get_manifest(
                    image_ref,
                    specific_digest=digest,
                    client=client,
                    insecure=insecure,
                )
                layers = await _layers_details(
                    image_ref, manifest, client, insecure=insecure
                )
                result.append(
                    {
                        "os": plat.get("os"),
                        "architecture": plat.get("architecture"),
                        "layers": layers,
                    }
                )
        else:
            layers = await _layers_details(
                image_ref, manifest_index, client, insecure=insecure
            )
        result.append(
            {
                "os": manifest_index.get("os"),
                "architecture": manifest_index.get("architecture"),
                "layers": layers,
            }
        )
        return result
