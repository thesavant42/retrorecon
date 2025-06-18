from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any, Dict, List

from flask import Blueprint, render_template, request, send_file
from aiohttp import ClientError
import asyncio

from layerslayer.utils import parse_image_ref, registry_base_url
from layerslayer.client import DockerRegistryClient, get_manifest, list_layer_files
from retrorecon.registry_explorer import fetch_token, fetch_blob

bp = Blueprint("oci", __name__)


@bp.route("/tools/registry_explorer", methods=["GET"])
def oci_index():
    return render_template("oci_index.html")


async def _repo_data(repo: str) -> Dict[str, Any]:
    user, repo_name = parse_image_ref(f"{repo}:latest")[:2]
    url = f"{registry_base_url(user, repo_name)}/tags/list"
    async with DockerRegistryClient() as client:
        data = await client.fetch_json(url, user, repo_name)
        tags = data.get("tags", [])
        manifests: Dict[str, Any] = {}
        for tag in tags:
            digest = await client.fetch_digest(
                f"{registry_base_url(user, repo_name)}/manifests/{tag}", user, repo_name
            )
            if digest:
                manifests.setdefault(digest, {"tag": []})["tag"].append(tag)
        return {"name": f"{repo}", "child": [], "tags": tags, "manifest": manifests}


@bp.route("/repo/<path:repo>", methods=["GET"])
def repo_view(repo: str):
    try:
        data = asyncio.run(_repo_data(repo))
    except asyncio.TimeoutError:
        return ("timeout", 504)
    except ClientError as exc:
        return (str(exc), 502)
    except Exception:
        return ("server error", 500)
    return render_template("oci_repo.html", repo=repo, data=data)


async def _image_data(image: str) -> Dict[str, Any]:
    """Return manifest or index information for ``image``."""
    async with DockerRegistryClient() as client:
        manifest = await get_manifest(image, client=client)
    return {"manifest": manifest}


async def _resolve_manifest(image: str) -> Dict[str, Any]:
    """Return a concrete manifest for ``image`` resolving indexes."""
    async with DockerRegistryClient() as client:
        manifest = await get_manifest(image, client=client)
        if manifest.get("manifests"):
            digest = manifest["manifests"][0]["digest"]
            manifest = await get_manifest(image, specific_digest=digest, client=client)
    return manifest


@bp.route("/image/<path:image>", methods=["GET"])
def image_view(image: str):
    try:
        data = asyncio.run(_image_data(image))
    except asyncio.TimeoutError:
        return ("timeout", 504)
    except ClientError as exc:
        return (str(exc), 502)
    except Exception:
        return ("server error", 500)
    return render_template("oci_image.html", image=image, data=data, title=image)


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


@bp.route("/fs/<path:repo>@<digest>", defaults={"subpath": ""}, methods=["GET"])
@bp.route("/fs/<path:repo>@<digest>/<path:subpath>", methods=["GET"])
def fs_view(repo: str, digest: str, subpath: str):
    render_mode = request.args.get("render")
    try:
        blob = asyncio.run(_read_layer(repo, digest))
    except asyncio.TimeoutError:
        return ("timeout", 504)
    except ClientError as exc:
        return (str(exc), 502)
    except Exception:
        return ("server error", 500)
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
        if not subpath:
            names = [m.name for m in tar.getmembers()]
            return render_template("oci_fs.html", repo=repo, digest=digest, path="", items=names)
        try:
            member = tar.getmember(subpath)
        except KeyError:
            return ("not found", 404)
        if member.isdir():
            names = [m.name for m in tar.getmembers() if m.name.startswith(subpath) and m.name != subpath]
            return render_template("oci_fs.html", repo=repo, digest=digest, path=subpath, items=names)
        file_obj = tar.extractfile(member)
        if not file_obj:
            return ("not found", 404)
        data = file_obj.read()
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


@bp.route("/layers/<path:image>/<path:subpath>", methods=["GET"])
def layer_dir(image: str, subpath: str):
    try:
        manifest = asyncio.run(_resolve_manifest(image))
    except Exception:
        return ("error", 500)
    layers = manifest.get("layers", [])
    if not layers:
        return ("no layers", 404)
    digest = layers[0]["digest"]
    repo = image.split(":")[0]
    return fs_view(repo, digest, subpath)
