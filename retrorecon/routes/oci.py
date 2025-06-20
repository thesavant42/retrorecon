from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime
import stat

from flask import Blueprint, render_template, request, send_file, current_app
from aiohttp import ClientError
import aiohttp
import asyncio

from layerslayer.utils import parse_image_ref, registry_base_url
from layerslayer.client import (
    DockerRegistryClient,
    get_manifest,
    get_manifest_digest,
    list_layer_files,
    DEFAULT_TIMEOUT,
)
from retrorecon.registry_explorer import fetch_token, fetch_blob
from layerslayer.utils import human_readable_size

bp = Blueprint("oci", __name__)


@bp.route("/tools/registry_explorer", methods=["GET"])
def oci_index():
    return render_template("oci_index.html")


async def _repo_data(repo: str) -> Dict[str, Any]:
    user, repo_name = parse_image_ref(f"{repo}:latest")[:2]
    base = registry_base_url(user, repo_name).rstrip("/")
    url = f"{base}/tags/list"

    # ``registry.k8s.io`` and similar public registries allow anonymous
    # access to ``/v2/tags/list`` which returns a list of child repositories.
    # ``DockerRegistryClient`` is hardcoded to use Docker Hub authentication
    # and fails for these registries. If ``repo_name`` is empty we perform a
    # simple anonymous request instead.
    if repo_name == "":
        async with aiohttp.ClientSession(timeout=DEFAULT_TIMEOUT, trust_env=True) as sess:
            async with sess.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
        return {
            "name": repo,
            "child": data.get("child", []),
            "tags": data.get("tags", []),
            "manifest": data.get("manifest", {}),
        }

    async with DockerRegistryClient() as client:
        data = await client.fetch_json(url, user, repo_name)
        tags = data.get("tags", [])
        manifests: Dict[str, Any] = {}
        for tag in tags:
            digest = await client.fetch_digest(
                f"{base}/manifests/{tag}", user, repo_name
            )
            if digest:
                manifests.setdefault(digest, {"tag": []})["tag"].append(tag)
        return {
            "name": repo,
            "child": data.get("child", []),
            "tags": tags,
            "manifest": manifests,
        }


@bp.route("/repo/<path:repo>", methods=["GET"])
def repo_view(repo: str):
    try:
        data = asyncio.run(_repo_data(repo))
    except asyncio.TimeoutError:
        return (
            render_template("oci_error.html", repo=repo, message="timeout"),
            504,
        )
    except ClientError as exc:
        return (
            render_template("oci_error.html", repo=repo, message=str(exc)),
            502,
        )
    except Exception:
        return (
            render_template("oci_error.html", repo=repo, message="server error"),
            500,
        )
    user, repo_name = parse_image_ref(f"{repo}:latest")[:2]
    data_url = f"{registry_base_url(user, repo_name).rstrip('/')}/tags/list"
    return render_template(
        "oci_repo.html",
        repo=repo,
        data=data,
        data_url=data_url,
    )


async def _image_data(image: str) -> Dict[str, Any]:
    """Return manifest or index information for ``image`` along with HTTP details."""
    async with DockerRegistryClient() as client:
        manifest = await get_manifest(image, client=client)
        digest = await get_manifest_digest(image, client=client)
    media_type = (
        "application/vnd.oci.image.index.v1+json"
        if manifest.get("manifests")
        else "application/vnd.oci.image.manifest.v1+json"
    )
    size = len(json.dumps(manifest))
    http_headers = {
        "Content-Type": media_type,
        "Docker-Content-Digest": digest or "",
        "Content-Length": str(size),
    }
    descriptor = {
        "mediaType": media_type,
        "digest": digest or "",
        "size": size,
    }
    return {"manifest": manifest, "headers": http_headers, "descriptor": descriptor}


async def _resolve_manifest(image: str) -> Dict[str, Any]:
    """Return a concrete manifest for ``image`` resolving indexes."""
    async with DockerRegistryClient() as client:
        manifest = await get_manifest(image, client=client)
        if manifest.get("manifests"):
            digest = manifest["manifests"][0]["digest"]
            manifest = await get_manifest(image, specific_digest=digest, client=client)
    return manifest


async def _image_data_digest(repo: str, digest: str) -> Dict[str, Any]:
    """Return manifest information for ``repo`` pinned to ``digest``."""
    image_ref = f"{repo}:latest"
    async with DockerRegistryClient() as client:
        manifest = await get_manifest(image_ref, specific_digest=digest, client=client)
    media_type = (
        "application/vnd.oci.image.index.v1+json"
        if manifest.get("manifests")
        else "application/vnd.oci.image.manifest.v1+json"
    )
    size = len(json.dumps(manifest))
    http_headers = {
        "Content-Type": media_type,
        "Docker-Content-Digest": digest,
        "Content-Length": str(size),
    }
    descriptor = {"mediaType": media_type, "digest": digest, "size": size}
    return {"manifest": manifest, "headers": http_headers, "descriptor": descriptor}


@bp.route("/image/<path:image>", methods=["GET"])
def image_view(image: str):
    try:
        data = asyncio.run(_image_data(image))
    except asyncio.TimeoutError:
        return (
            render_template("oci_error.html", image=image, message="timeout"),
            504,
        )
    except ClientError as exc:
        return (
            render_template("oci_error.html", image=image, message=str(exc)),
            502,
        )
    except Exception:
        return (
            render_template("oci_error.html", image=image, message="server error"),
            500,
        )
    return render_template("oci_image.html", image=image, data=data, title=image)


@bp.route("/image/<path:repo>@<digest>", methods=["GET"])
def image_digest_view(repo: str, digest: str):
    display = f"{repo}@{digest}"
    try:
        data = asyncio.run(_image_data_digest(repo, digest))
    except asyncio.TimeoutError:
        return (
            render_template("oci_error.html", image=display, message="timeout"),
            504,
        )
    except ClientError as exc:
        return (
            render_template("oci_error.html", image=display, message=str(exc)),
            502,
        )
    except Exception:
        return (
            render_template("oci_error.html", image=display, message="server error"),
            500,
        )
    return render_template(
        "oci_image.html",
        image=repo,
        display_image=display,
        data=data,
        title=display,
    )


async def _read_layer(repo: str, digest: str) -> bytes:
    token = await fetch_token(repo)
    return await fetch_blob(repo, digest, token)


def _hexdump(data: bytes) -> str:
    hex_lines = []
    for i in range(0, len(data), 16):
        chunk = data[i : i + 16]
        hex_bytes = " ".join(f"{b:02x}" for b in chunk)
        text = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        hex_lines.append(f"{i:08x}: {hex_bytes:<47} {text}")
    return "\n".join(hex_lines)


@bp.route("/size/<path:repo>@<digest>", methods=["GET"])
def layer_size_view(repo: str, digest: str):
    """Return a formatted directory listing for the layer blob."""
    try:
        blob = asyncio.run(_read_layer(repo, digest))
    except asyncio.TimeoutError:
        return (
            render_template("oci_error.html", repo=repo, message="timeout"),
            504,
        )
    except ClientError as exc:
        return (
            render_template("oci_error.html", repo=repo, message=str(exc)),
            502,
        )
    except Exception:
        return (
            render_template("oci_error.html", repo=repo, message="server error"),
            500,
        )

    entries = []
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
            for m in tar.getmembers():
                mode = m.mode
                if m.isfile():
                    mode |= stat.S_IFREG
                elif m.isdir():
                    mode |= stat.S_IFDIR
                elif m.issym():
                    mode |= stat.S_IFLNK
                perms = stat.filemode(mode)
                ts = datetime.utcfromtimestamp(m.mtime).strftime("%Y-%m-%d %H:%M")
                entries.append((m.size, f"{perms} {m.uid}/{m.gid} {m.size} {ts} {m.name}"))
    except tarfile.TarError:
        current_app.logger.warning("invalid tar for %s@%s", repo, digest)
        return (
            render_template("oci_error.html", repo=repo, digest=digest, message="invalid tar"),
            415,
        )

    entries.sort(key=lambda x: x[0], reverse=True)
    lines = [e[1] for e in entries]

    mt = request.args.get("mt", "application/vnd.docker.image.rootfs.diff.tar.gzip")
    size_param = request.args.get("size")
    blob_size = int(size_param) if size_param else len(blob)
    size_hr = human_readable_size(blob_size)

    return render_template(
        "oci_layer.html",
        repo=repo,
        digest=digest,
        media_type=mt,
        size=blob_size,
        size_hr=size_hr,
        lines=lines,
        title=f"{repo}@{digest}",
    )


def _list_children(tar: tarfile.TarFile, subpath: str) -> list[dict[str, Any]]:
    prefix = subpath.rstrip("/")
    if prefix:
        prefix += "/"
    mapping: dict[str, bool] = {}
    for m in tar.getmembers():
        if not m.name.startswith(prefix) or m.name == subpath.rstrip("/"):
            continue
        remainder = m.name[len(prefix) :]
        part = remainder.split("/", 1)[0]
        if not part:
            continue
        is_dir = "/" in remainder or m.isdir()
        mapping[part] = mapping.get(part, False) or is_dir
    items = []
    for name in sorted(mapping):
        child_path = prefix + name
        if mapping[name] and not child_path.endswith("/"):
            child_path += "/"
        items.append({"name": name, "path": child_path, "is_dir": mapping[name]})
    return items


@bp.route("/fs/<path:repo>@<digest>", defaults={"subpath": ""}, methods=["GET"])
@bp.route("/fs/<path:repo>@<digest>/<path:subpath>", methods=["GET"])
def fs_view(repo: str, digest: str, subpath: str):
    render_mode = request.args.get("render")
    q = request.args.get("q", "")
    q_lower = q.lower()
    try:
        blob = asyncio.run(_read_layer(repo, digest))
    except asyncio.TimeoutError:
        return (
            render_template("oci_error.html", repo=repo, message="timeout"),
            504,
        )
    except ClientError as exc:
        return (
            render_template("oci_error.html", repo=repo, message=str(exc)),
            502,
        )
    except Exception:
        return (
            render_template("oci_error.html", repo=repo, message="server error"),
            500,
        )
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
            if not subpath or subpath.endswith("/"):
                items = _list_children(tar, subpath)
                if q:
                    items = [it for it in items if q_lower in it["name"].lower()]
                disp = "/" + subpath.rstrip("/") if subpath else "/"
                return render_template(
                    "oci_fs.html",
                    repo=repo,
                    digest=digest,
                    path=disp,
                    items=items,
                    q=q,
                )
            try:
                member = tar.getmember(subpath)
            except KeyError:
                return ("not found", 404)
            if member.isdir():
                items = _list_children(tar, subpath)
                if q:
                    items = [it for it in items if q_lower in it["name"].lower()]
                return render_template(
                    "oci_fs.html",
                    repo=repo,
                    digest=digest,
                    path="/" + subpath.rstrip("/"),
                    items=items,
                    q=q,
                )
            file_obj = tar.extractfile(member)
            if not file_obj:
                return ("not found", 404)
            data = file_obj.read()
    except tarfile.TarError:
        current_app.logger.warning("invalid tar for %s@%s", repo, digest)
        return (
            render_template("oci_error.html", repo=repo, digest=digest, message="invalid tar"),
            415,
        )
    if render_mode == "hex":
        return render_template("oci_hex.html", data=_hexdump(data), path=subpath)
    if render_mode == "elf":
        try:
            from elftools.elf.elffile import ELFFile
        except Exception:
            return ("elf support missing", 500)
        f = io.BytesIO(data)
        try:
            elf = ELFFile(f)
            info = {"class": elf.elfclass, "entry": elf.header["e_entry"]}
        except Exception:
            info = {"error": "invalid elf"}
        return render_template("oci_elf.html", info=json.dumps(info, indent=2), path=subpath)
    return send_file(io.BytesIO(data), download_name=Path(subpath).name, as_attachment=False)


def _parse_ls_line(line: str) -> tuple[str, bool]:
    parts = line.split(None, 4)
    if len(parts) < 5:
        return "", False
    return parts[4], parts[0].startswith("d")


async def _build_overlay(image: str) -> dict[str, tuple[str, bool]]:
    async with DockerRegistryClient() as client:
        manifest = await get_manifest(image, client=client)
        if manifest.get("manifests"):
            digest = manifest["manifests"][0]["digest"]
            manifest = await get_manifest(image, specific_digest=digest, client=client)
        mapping: dict[str, tuple[str, bool]] = {}
        for layer in manifest.get("layers", []):
            files = await list_layer_files(image, layer["digest"], client=client)
            for line in files:
                path, is_dir = _parse_ls_line(line)
                if path:
                    mapping[path] = (layer["digest"], is_dir)
        return mapping


def _overlay_view(image: str, digest: str, subpath: str):
    overlay = asyncio.run(_build_overlay(image))
    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"
    entry = overlay.get(subpath)
    if entry and not entry[1]:
        return fs_view(repo_full, entry[0], subpath)

    q = request.args.get("q", "")
    q_lower = q.lower()
    prefix = subpath.rstrip("/")
    if prefix:
        prefix += "/"
    mapping: dict[str, bool] = {}
    for path in overlay:
        if not path.startswith(prefix) or path == subpath:
            continue
        remainder = path[len(prefix):]
        part = remainder.split("/", 1)[0]
        is_dir = "/" in remainder or overlay.get(prefix + part, ("", False))[1]
        mapping[part] = mapping.get(part, False) or is_dir
    items = []
    for name in sorted(mapping):
        if q and q_lower not in name.lower():
            continue
        child_path = prefix + name
        if mapping[name] and not child_path.endswith("/"):
            child_path += "/"
        items.append({"name": name, "path": child_path, "is_dir": mapping[name]})
    return render_template(
        "oci_fs.html",
        repo=repo_full,
        digest=digest,
        path="/" + subpath.rstrip("/") if subpath else "/",
        items=items,
        q=q,
    )


@bp.route("/layers/<path:image>/<path:subpath>", methods=["GET"])
def layer_dir(image: str, subpath: str):
    try:
        manifest = asyncio.run(_resolve_manifest(image))
    except Exception:
        return (
            render_template("oci_error.html", image=image, message="error"),
            500,
        )
    layers = manifest.get("layers", [])
    if not layers:
        return (
            render_template("oci_error.html", image=image, message="no layers"),
            404,
        )
    digest = layers[0]["digest"]
    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"
    return fs_view(repo_full, digest, subpath)


@bp.route("/layers/<path:image>@<digest>/", defaults={"subpath": ""}, methods=["GET"])
@bp.route("/layers/<path:image>@<digest>/<path:subpath>", methods=["GET"])
def layer_digest_dir(image: str, digest: str, subpath: str):
    """Browse ``digest`` from ``image`` starting at ``subpath``."""
    try:
        manifest_digest = asyncio.run(get_manifest_digest(image))
    except Exception:
        manifest_digest = ""
    if digest == manifest_digest:
        return _overlay_view(image, digest, subpath)

    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"
    return fs_view(repo_full, digest, subpath)
