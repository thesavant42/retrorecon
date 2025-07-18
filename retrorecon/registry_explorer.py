"""Registry Explorer API module ported from the Docker Registry Explorer extension."""
from __future__ import annotations

import asyncio
import io
import re
import tarfile
from datetime import datetime
import stat
from typing import Any, Dict, List, Optional

import aiohttp
from aiohttp import ClientConnectorCertificateError

from layerslayer.utils import parse_image_ref

DEFAULT_DOMAIN = "registry-1.docker.io"
LEGACY_DEFAULT_DOMAIN = "index.docker.io"
OFFICIAL_REPO_NAME = "library"

DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=120)


def _new_session(insecure: bool = False) -> aiohttp.ClientSession:
    """Return a new :class:`aiohttp.ClientSession` respecting ``insecure``."""
    if insecure:
        connector = aiohttp.TCPConnector(ssl=False)
        return aiohttp.ClientSession(
            timeout=DEFAULT_TIMEOUT, connector=connector, trust_env=True
        )
    return aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT, trust_env=True)


def split_docker_domain(name: str) -> tuple[str, str]:
    """Return (domain, remainder) for a Docker image reference."""
    i = name.find("/")
    first = name[:i]
    if i == -1 or ("." not in first and ":" not in first and first != "localhost"):
        domain = DEFAULT_DOMAIN
        remainder = name
    else:
        domain = first
        remainder = name[i + 1 :]
    if domain == LEGACY_DEFAULT_DOMAIN:
        domain = DEFAULT_DOMAIN
    if domain == DEFAULT_DOMAIN and "/" not in remainder:
        remainder = f"{OFFICIAL_REPO_NAME}/{remainder}"
    return domain, remainder


async def fetch_token(
    repo: str,
    session: Optional[aiohttp.ClientSession] = None,
    *,
    insecure: bool = False,
) -> str:
    """Fetch an anonymous pull token for the given repository."""
    domain, remainder = split_docker_domain(repo)

    async def _do(sess: aiohttp.ClientSession) -> str:
        async with sess.get(f"https://{domain}/v2/") as resp:
            auth = resp.headers.get("www-authenticate")
        realm = "https://auth.docker.io/token"
        service = "registry.docker.io"
        if auth:
            m = re.search(r'realm="([^"]+)"', auth)
            if m:
                realm = m.group(1)
            m = re.search(r'service="([^"]+)"', auth)
            if m:
                service = m.group(1)
        async with sess.get(
            f"{realm}?service={service}&scope=repository:{remainder}:pull"
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data.get("token", "")

    if session is not None:
        return await _do(session)
    async with _new_session(insecure) as sess:
        return await _do(sess)


ACCEPT_HEADERS = (
    "application/vnd.oci.image.index.v1+json,"
    "application/vnd.oci.image.manifest.v1+json,"
    "application/vnd.docker.distribution.manifest.list.v2+json,"
    "application/vnd.docker.distribution.manifest.v2+json"
)


async def fetch_index_or_manifest(
    repo: str,
    digest_or_tag: str,
    token: str,
    session: Optional[aiohttp.ClientSession] = None,
    *,
    insecure: bool = False,
) -> Dict[str, Any]:
    domain, remainder = split_docker_domain(repo)
    url = f"https://{domain}/v2/{remainder}/manifests/{digest_or_tag}"
    headers = {"Accept": ACCEPT_HEADERS, "Authorization": f"Bearer {token}"}

    async def _do(sess: aiohttp.ClientSession) -> Dict[str, Any]:
        async with sess.get(url, headers=headers) as resp:
            resp.raise_for_status()
            body = await resp.json()
            return {
                "digest": resp.headers.get("docker-content-digest"),
                "contentType": resp.headers.get("content-type"),
                "_digestOrTag": digest_or_tag,
                **body,
            }

    if session is not None:
        return await _do(session)
    async with _new_session(insecure) as sess:
        return await _do(sess)


async def fetch_blob(
    repo: str,
    digest: str,
    token: str,
    session: Optional[aiohttp.ClientSession] = None,
    *,
    insecure: bool = False,
) -> bytes:
    domain, remainder = split_docker_domain(repo)
    url = f"https://{domain}/v2/{remainder}/blobs/{digest}"
    headers = {"Authorization": f"Bearer {token}"}

    async def _do(sess: aiohttp.ClientSession) -> bytes:
        async with sess.get(url, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.read()

    if session is not None:
        return await _do(session)
    async with _new_session(insecure) as sess:
        return await _do(sess)


async def list_layer_files(
    repo: str,
    digest: str,
    token: str,
    session: Optional[aiohttp.ClientSession] = None,
    *,
    insecure: bool = False,
) -> List[str]:
    """Return formatted file listing for the layer blob."""
    data = await fetch_blob(repo, digest, token, session, insecure=insecure)
    tar_bytes = io.BytesIO(data)

    def _format(ti: tarfile.TarInfo) -> str:
        mode = ti.mode
        if ti.isfile():
            mode |= stat.S_IFREG
        elif ti.isdir():
            mode |= stat.S_IFDIR
        elif ti.issym():
            mode |= stat.S_IFLNK
        perms = stat.filemode(mode)
        ts = datetime.utcfromtimestamp(ti.mtime).strftime("%Y-%m-%d %H:%M")
        return f"{perms} {ti.uid}/{ti.gid} {ti.size} {ts} {ti.name}"

    try:
        with tarfile.open(fileobj=tar_bytes, mode="r:*") as tar:
            return [_format(m) for m in tar.getmembers()]
    except tarfile.ReadError:
        return []


async def get_manifest_digest(
    image_ref: str,
    token: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None,
    *,
    insecure: bool = False,
) -> Optional[str]:
    user, repo, tag = parse_image_ref(image_ref)
    repo_full = f"{user}/{repo}"
    token = token or await fetch_token(repo_full, session, insecure=insecure)
    domain, remainder = split_docker_domain(repo_full)
    url = f"https://{domain}/v2/{remainder}/manifests/{tag}"
    headers = {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        "Authorization": f"Bearer {token}",
    }
    async def _do(sess: aiohttp.ClientSession) -> Optional[str]:
        async with sess.head(url, headers=headers) as resp:
            resp.raise_for_status()
            return resp.headers.get("Docker-Content-Digest")

    if session is not None:
        return await _do(session)
    async with _new_session(insecure) as sess:
        return await _do(sess)


async def _layers_details(
    repo: str,
    manifest: Dict[str, Any],
    token: str,
    session: aiohttp.ClientSession,
    fetch_files: bool = True,
    *,
    insecure: bool = False,
) -> List[Dict[str, Any]]:
    """Return layer metadata and optionally file lists."""
    layers = manifest.get("layers", [])
    details: List[Dict[str, Any]] = []
    for layer in layers:
        files: List[str] = []
        if fetch_files:
            files = await list_layer_files(
                repo, layer["digest"], token, session, insecure=insecure
            )
        details.append(
            {
                "digest": layer["digest"],
                "size": layer.get("size", 0),
                "files": files,
            }
        )
    return details


async def gather_image_info(
    image_ref: str,
    fetch_files: bool = True,
    *,
    insecure: bool = False,
) -> List[Dict[str, Any]]:
    """Gather layer details for an image using direct registry calls."""
    user, repo, tag = parse_image_ref(image_ref)
    repo_full = f"{user}/{repo}"
    async with _new_session(insecure) as session:
        token = await fetch_token(repo_full, session, insecure=insecure)
        root = await fetch_index_or_manifest(
            repo_full, tag, token, session, insecure=insecure
        )
        result: List[Dict[str, Any]] = []
        if root.get("manifests"):
            for m in root["manifests"]:
                plat = m.get("platform", {})
                digest = m["digest"]
                manifest = await fetch_index_or_manifest(
                    repo_full, digest, token, session, insecure=insecure
                )
                layers = await _layers_details(
                    repo_full,
                    manifest,
                    token,
                    session,
                    fetch_files=fetch_files,
                    insecure=insecure,
                )
                result.append({"os": plat.get("os"), "architecture": plat.get("architecture"), "layers": layers})
        else:
            layers = await _layers_details(
                repo_full,
                root,
                token,
                session,
                fetch_files=fetch_files,
                insecure=insecure,
            )
            result.append({"os": root.get("os"), "architecture": root.get("architecture"), "layers": layers})
        return result



async def gather_image_info_with_backend(
    image_ref: str,
    method: str = "layerslayer",
    *,
    fetch_files: bool = True,
    insecure: bool = False,
) -> List[Dict[str, Any]]:
    """Return layer info using the selected backend."""
    if method == "layerslayer":
        from .docker_layers import gather_layers_info as gl
        if fetch_files:
            return await gl(image_ref)
        # Fall back to direct registry calls without files
        return await gather_image_info(image_ref, fetch_files=False, insecure=insecure)
    if method in {"layertools", "extension"}:
        return await gather_image_info(image_ref, fetch_files=fetch_files, insecure=insecure)
    raise ValueError(f"unknown method: {method}")


async def gather_image_info_multi(
    image_ref: str,
    methods: List[str],
    *,
    fetch_files: bool = True,
    insecure: bool = False,
) -> Dict[str, List[Dict[str, Any]]]:
    """Run :func:`gather_image_info_with_backend` for all ``methods`` in parallel."""
    tasks = {
        m: asyncio.create_task(
            gather_image_info_with_backend(
                image_ref, m, fetch_files=fetch_files, insecure=insecure
            )
        )
        for m in methods
    }
    results: Dict[str, List[Dict[str, Any]]] = {}
    for method, task in tasks.items():
        try:
            results[method] = await task
        except Exception as exc:  # pragma: no cover - unexpected
            results[method] = [{"error": str(exc)}]
    return results


def detect_address_type(address: str) -> str:
    """Return ``'repo'`` or ``'image'`` for ``address``.

    Addresses lacking a tag or digest are treated as repositories.
    Anything with a tag (``name:tag``) or digest (``name@sha256:...``)
    is classified as an image reference.
    """

    if "@" in address:
        return "image"
    if ":" in address and address.rfind(":") > address.rfind("/"):
        return "image"
    return "repo"


def _add_to_tree(tree: Dict[str, Any], path: str) -> None:
    parts = path.split("/")
    node = tree
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node.setdefault("files", []).append(parts[-1])


def manifest_to_table(platforms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert layer listings to a hierarchical tree structure."""

    result: List[Dict[str, Any]] = []
    for plat in platforms:
        plat_entry = {
            "os": plat.get("os"),
            "architecture": plat.get("architecture"),
            "layers": [],
        }
        for layer in plat.get("layers", []):
            tree: Dict[str, Any] = {}
            for file_path in layer.get("files", []):
                _add_to_tree(tree, file_path)
            plat_entry["layers"].append(
                {
                    "digest": layer.get("digest"),
                    "size": layer.get("size"),
                    "tree": tree,
                }
            )
        result.append(plat_entry)
    return result
