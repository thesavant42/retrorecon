from __future__ import annotations

import asyncio
import io
import tarfile
from pathlib import Path
from typing import Any, Dict

from aiohttp import ClientError
from flask import Blueprint, jsonify, render_template, request, send_file

import app
from layerslayer.client import DockerRegistryClient, get_manifest, list_layer_files
from layerslayer.utils import parse_image_ref, registry_base_url

bp = Blueprint("dag", __name__)


def _split_repo(name: str) -> tuple[str, str]:
    if "/" in name:
        return tuple(name.split("/", 1))  # type: ignore[return-value]
    return "library", name


@bp.route("/dag_explorer", methods=["GET"])
def dag_explorer_page():
    return render_template("dag_explorer.html")


@bp.route("/tools/dag_explorer", methods=["GET"])
def dag_explorer_full_page():
    """Serve the main dashboard so the overlay can open on load."""
    return app.index()


@bp.route("/dag/repo/<path:repo>", methods=["GET"])
def dag_repo(repo: str):
    async def _fetch() -> Dict[str, Any]:
        user, repo_name = _split_repo(repo)
        url = f"{registry_base_url(user, repo_name)}/tags/list"
        async with DockerRegistryClient() as client:
            return await client.fetch_json(url, user, repo_name)

    try:
        data = asyncio.run(_fetch())
    except asyncio.TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except ClientError as exc:
        return jsonify({"error": "client_error", "details": str(exc)}), 502
    except Exception as exc:  # pragma: no cover - unexpected
        return jsonify({"error": "server_error", "details": str(exc)}), 500
    return jsonify(data)


@bp.route("/dag/image/<path:image>", methods=["GET"])
def dag_image(image: str):
    async def _fetch() -> Dict[str, Any]:
        async with DockerRegistryClient() as client:
            return await get_manifest(image, client=client)

    try:
        data = asyncio.run(_fetch())
    except asyncio.TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except ClientError as exc:
        return jsonify({"error": "client_error", "details": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": "server_error", "details": str(exc)}), 500
    return jsonify(data)


@bp.route("/dag/fs/<path:image>@<digest>/<path:path>", methods=["GET"])
def dag_fs(image: str, digest: str, path: str):

    async def _fetch() -> bytes:
        user, repo, _ = parse_image_ref(image)
        url = f"{registry_base_url(user, repo)}/blobs/{digest}"
        async with DockerRegistryClient() as client:
            return await client.fetch_bytes(url, user, repo)

    try:
        blob = asyncio.run(_fetch())
    except asyncio.TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except ClientError as exc:
        return jsonify({"error": "client_error", "details": str(exc)}), 502
    except Exception as exc:
        return jsonify({"error": "server_error", "details": str(exc)}), 500

    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tar:
            try:
                member = tar.getmember(path)
            except KeyError:
                return jsonify({"error": "not_found"}), 404
            file_obj = tar.extractfile(member)
            if not file_obj:
                return jsonify({"error": "not_found"}), 404
            data = file_obj.read()
    except tarfile.TarError:
        app.logger.warning("invalid tar blob for %s at %s", image, digest)
        return jsonify({"error": "invalid_blob"}), 415
    filename = Path(path).name
    return send_file(io.BytesIO(data), download_name=filename, as_attachment=False)


@bp.route("/dag/layer/<path:image>@<digest>", methods=["GET"])
def dag_layer(image: str, digest: str):

    async def _fetch() -> list[str]:
        async with DockerRegistryClient() as client:
            return await list_layer_files(image, digest, client=client)

    try:
        files = asyncio.run(_fetch())
    except asyncio.TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except ClientError as exc:
        return jsonify({"error": "client_error", "details": str(exc)}), 502
    except Exception as exc:  # pragma: no cover - unexpected
        return jsonify({"error": "server_error", "details": str(exc)}), 500
    return jsonify({"files": files})
