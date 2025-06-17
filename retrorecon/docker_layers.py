import asyncio
import io
import tarfile
from typing import Any, Dict, List, Optional
import os

import aiohttp

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(
    total=int(os.environ.get("REGISTRY_TIMEOUT", "120"))
)

from layerslayer.utils import (
    parse_image_ref,
    registry_base_url,
    human_readable_size,
)


class DockerRegistryClient:
    """Async Docker registry client with simple token caching."""

    def __init__(self) -> None:
        self.session: Optional[aiohttp.ClientSession] = None
        self.token_cache: Dict[str, str] = {}

    async def __aenter__(self) -> "DockerRegistryClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def _fetch_token(self, user: str, repo: str) -> Optional[str]:
        auth_url = (
            f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{user}/{repo}:pull"
        )
        async with aiohttp.ClientSession(trust_env=True) as sess:
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
        headers = {
            "Accept": "application/vnd.docker.distribution.manifest.v2+json"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def fetch_json(self, url: str, user: str, repo: str) -> Dict[str, Any]:
        headers = await self._auth_headers(user, repo)
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=DEFAULT_TIMEOUT,
                trust_env=True
            )
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
            self.session = aiohttp.ClientSession(
                timeout=DEFAULT_TIMEOUT,
                trust_env=True
            )
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
            self.session = aiohttp.ClientSession(
                timeout=DEFAULT_TIMEOUT,
                trust_env=True
            )
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



def get_client() -> DockerRegistryClient:
    """Return a fresh DockerRegistryClient instance."""
    return DockerRegistryClient()


async def get_manifest_digest(
    image_ref: str,
    client: Optional[DockerRegistryClient] = None,
) -> Optional[str]:
    user, repo, tag = parse_image_ref(image_ref)
    url = f"{registry_base_url(user, repo)}/manifests/{tag}"
    c = client or get_client()
    return await c.fetch_digest(url, user, repo)


async def get_manifest(
    image_ref: str,
    specific_digest: Optional[str] = None,
    client: Optional[DockerRegistryClient] = None,
) -> Dict[str, Any]:
    user, repo, tag = parse_image_ref(image_ref)
    ref = specific_digest or tag
    url = f"{registry_base_url(user, repo)}/manifests/{ref}"
    c = client or get_client()
    return await c.fetch_json(url, user, repo)


async def list_layer_files(
    image_ref: str,
    digest: str,
    client: Optional[DockerRegistryClient] = None,
) -> List[str]:
    """Return the list of files contained in a layer blob.

    The function first attempts ranged GET requests to avoid downloading large
    layers in full. If the collected bytes cannot be parsed as a tar archive it
    falls back to downloading the entire blob via ``fetch_bytes``.
    """
    user, repo, _ = parse_image_ref(image_ref)
    url = f"{registry_base_url(user, repo)}/blobs/{digest}"
    c = client or get_client()

    headers = await c._auth_headers(user, repo)
    headers["Accept"] = "*/*"
    if c.session is None:
        c.session = aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT, trust_env=True)

    range_size = int(os.environ.get("LAYERPEEK_RANGE", "2097152"))

    def _parse(data: bytes) -> List[str]:
        tar_bytes = io.BytesIO(data)
        with tarfile.open(fileobj=tar_bytes, mode="r:*") as tar:
            return [m.name for m in tar.getmembers()]

    # range_size <= 0 means fetch the whole blob immediately
    if range_size <= 0:
        data = await c.fetch_bytes(url, user, repo)
        return _parse(data)

    start = 0
    data = bytearray()
    while True:
        h = dict(headers)
        h["Range"] = f"bytes={start}-{start + range_size - 1}"
        async with c.session.get(url, headers=h) as resp:
            if resp.status == 416:
                break
            resp.raise_for_status()
            chunk = await resp.read()
            if not chunk:
                break
            data.extend(chunk)
        try:
            return _parse(data)
        except tarfile.ReadError:
            if len(chunk) < range_size:
                break
            start += range_size
            continue
    try:
        return _parse(data)
    except tarfile.ReadError:
        # Final attempt failed → download the entire blob and parse
        try:
            data = await c.fetch_bytes(url, user, repo)
            return _parse(data)
        except Exception:
            return []


async def _layers_details(
    image_ref: str,
    manifest: Dict[str, Any],
    client: DockerRegistryClient,
) -> List[Dict[str, Any]]:
    layers = manifest.get("layers", [])
    details: List[Dict[str, Any]] = []
    for layer in layers:
        try:
            files = await list_layer_files(image_ref, layer["digest"], client)
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


async def gather_layers_info(image_ref: str) -> List[Dict[str, Any]]:
    async with DockerRegistryClient() as client:
        manifest_index = await get_manifest(image_ref, client=client)
        result: List[Dict[str, Any]] = []
        if manifest_index.get("manifests"):
            platforms = manifest_index["manifests"]
            for m in platforms:
                plat = m.get("platform", {})
                digest = m["digest"]
                manifest = await get_manifest(
                    image_ref, specific_digest=digest, client=client
                )
                layers = await _layers_details(image_ref, manifest, client)
                result.append(
                    {
                        "os": plat.get("os"),
                        "architecture": plat.get("architecture"),
                        "layers": layers,
                    }
                )
        else:
            layers = await _layers_details(image_ref, manifest_index, client)
            result.append(
                {
                    "os": manifest_index.get("os"),
                    "architecture": manifest_index.get("architecture"),
                    "layers": layers,
                }
            )
        return result

