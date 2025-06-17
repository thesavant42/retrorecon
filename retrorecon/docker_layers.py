import asyncio
import io
import tarfile
from typing import Any, Dict, List, Optional

import aiohttp

from .layerslayer_utils import parse_image_ref, registry_base_url


class DockerRegistryClient:
    """Async Docker registry client with simple token caching."""

    def __init__(self) -> None:
        self.session: Optional[aiohttp.ClientSession] = None
        self.token_cache: Dict[str, str] = {}

    async def close(self) -> None:
        if self.session:
            await self.session.close()

    async def _fetch_token(self, user: str, repo: str) -> Optional[str]:
        auth_url = (
            f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:{user}/{repo}:pull"
        )
        async with aiohttp.ClientSession() as sess:
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
                timeout=aiohttp.ClientTimeout(total=20)
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
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=20)
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


_client: Optional[DockerRegistryClient] = None


def get_client() -> DockerRegistryClient:
    global _client
    if _client is None:
        _client = DockerRegistryClient()
    return _client


async def get_manifest(image_ref: str, specific_digest: Optional[str] = None) -> Dict[str, Any]:
    user, repo, tag = parse_image_ref(image_ref)
    ref = specific_digest or tag
    url = f"{registry_base_url(user, repo)}/manifests/{ref}"
    return await get_client().fetch_json(url, user, repo)


async def list_layer_files(image_ref: str, digest: str) -> List[str]:
    user, repo, _ = parse_image_ref(image_ref)
    url = f"{registry_base_url(user, repo)}/blobs/{digest}"
    data = await get_client().fetch_bytes(url, user, repo)
    tar_bytes = io.BytesIO(data)
    files: List[str] = []
    with tarfile.open(fileobj=tar_bytes, mode="r:gz") as tar:
        for member in tar.getmembers():
            files.append(member.name)
    return files


async def _layers_details(image_ref: str, manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    layers = manifest.get("layers", [])
    tasks = [list_layer_files(image_ref, layer["digest"]) for layer in layers]
    files_list = await asyncio.gather(*tasks)
    details = []
    for layer, files in zip(layers, files_list):
        details.append(
            {
                "digest": layer["digest"],
                "size": layer.get("size"),
                "files": files,
            }
        )
    return details


async def gather_layers_info(image_ref: str) -> List[Dict[str, Any]]:
    manifest_index = await get_manifest(image_ref)
    result: List[Dict[str, Any]] = []
    if manifest_index.get("manifests"):
        platforms = manifest_index["manifests"]
        for m in platforms:
            plat = m.get("platform", {})
            digest = m["digest"]
            manifest = await get_manifest(image_ref, specific_digest=digest)
            layers = await _layers_details(image_ref, manifest)
            result.append(
                {
                    "os": plat.get("os"),
                    "architecture": plat.get("architecture"),
                    "layers": layers,
                }
            )
    else:
        layers = await _layers_details(image_ref, manifest_index)
        result.append(
            {
                "os": manifest_index.get("os"),
                "architecture": manifest_index.get("architecture"),
                "layers": layers,
            }
        )
    return result

