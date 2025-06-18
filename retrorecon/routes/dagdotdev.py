from __future__ import annotations

import asyncio
from aiohttp import ClientError
from flask import Blueprint, jsonify, request

from . import oci, dag
from layerslayer.client import DockerRegistryClient
from layerslayer.utils import parse_image_ref, registry_base_url

bp = Blueprint("dagdotdev", __name__)


@bp.route("/r/<path:ref>", methods=["GET"])
def r_route(ref: str):
    """Alias for repository or image views."""
    if ":" in ref or "@" in ref:
        return oci.image_view(ref)
    return oci.repo_view(ref)


@bp.route("/fs/<digest>/<path:path>", methods=["GET"])
def fs_route(digest: str, path: str):
    """Alias for ``/dag/fs`` route."""
    return dag.dag_fs(digest, path)


@bp.route("/layer/<digest>", methods=["GET"])
def layer_route(digest: str):
    """Alias for ``/dag/layer`` route."""
    return dag.dag_layer(digest)


@bp.route("/size/<digest>", methods=["GET"])
def size_route(digest: str):
    """Return the byte size of ``digest`` for ``image`` query."""
    image = request.args.get("image")
    if not image:
        return jsonify({"error": "missing_image"}), 400

    async def _fetch() -> int:
        user, repo, _ = parse_image_ref(image)
        url = f"{registry_base_url(user, repo)}/blobs/{digest}"
        async with DockerRegistryClient() as client:
            data = await client.fetch_bytes(url, user, repo)
            return len(data)

    try:
        size = asyncio.run(_fetch())
    except asyncio.TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except ClientError as exc:
        return jsonify({"error": "client_error", "details": str(exc)}), 502
    except Exception as exc:  # pragma: no cover - unexpected
        return jsonify({"error": "server_error", "details": str(exc)}), 500
    return jsonify({"size": size})
