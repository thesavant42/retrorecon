from flask import Blueprint, request, jsonify, send_file
import io
import asyncio
from aiohttp import ClientError
from aiohttp import ClientConnectorCertificateError

from ..docker_layers import (
    gather_layers_info,
    get_manifest_digest,
    DockerRegistryClient,
)
from layerslayer.utils import parse_image_ref, registry_base_url

bp = Blueprint("docker", __name__)


@bp.route("/docker_layers", methods=["GET"])
def docker_layers_route():
    image = request.args.get("image")
    insecure_flag = request.args.get("insecure", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if not image:
        return jsonify({"error": "missing_image"}), 400
    try:
        data = asyncio.run(gather_layers_info(image, insecure=insecure_flag))
        manifest = asyncio.run(get_manifest_digest(image, insecure=insecure_flag))
    except asyncio.TimeoutError:
        return jsonify({"error": "timeout"}), 504
    except ClientConnectorCertificateError:
        if not insecure_flag:
            try:
                data = asyncio.run(gather_layers_info(image, insecure=True))
                manifest = asyncio.run(get_manifest_digest(image, insecure=True))
                insecure_flag = True
            except Exception as exc:
                return jsonify({"error": "client_error", "details": str(exc)}), 502
        else:
            return jsonify({"error": "client_error", "details": "ssl_error"}), 502
    except ClientError as exc:
        return jsonify({"error": "client_error", "details": str(exc)}), 502
    except Exception as exc:  # pragma: no cover - unexpected
        return jsonify({"error": "server_error", "details": str(exc)}), 500
    for plat in data:
        for layer in plat["layers"]:
            layer["download"] = (
                request.url_root.rstrip("/")
                + "/download_layer?image="
                + image
                + "&digest="
                + layer["digest"]
            )
    owner, repo, tag = parse_image_ref(image)
    result = {
        "owner": owner,
        "repo": repo,
        "tag": tag,
        "manifest": manifest,
        "platforms": data,
        "insecure": insecure_flag,
    }
    return jsonify(result)


@bp.route("/download_layer", methods=["GET"])
def download_layer_route():
    image = request.args.get("image")
    digest = request.args.get("digest")
    insecure_flag = request.args.get("insecure", "false").lower() in {
        "1",
        "true",
        "yes",
    }
    if not image or not digest:
        return ("", 400)
    user, repo, _ = parse_image_ref(image)
    url = f"{registry_base_url(user, repo)}/blobs/{digest}"

    async def _fetch(insecure: bool) -> bytes:
        async with DockerRegistryClient(insecure=insecure) as client:
            return await client.fetch_bytes(url, user, repo)

    try:
        data = asyncio.run(_fetch(insecure_flag))
    except asyncio.TimeoutError:
        return ("", 504)
    except ClientConnectorCertificateError:
        if not insecure_flag:
            try:
                data = asyncio.run(_fetch(True))
                insecure_flag = True
            except Exception as exc:
                return (str(exc), 502)
        else:
            return ("ssl_error", 502)
    except ClientError as exc:
        return (str(exc), 502)
    except Exception:
        return ("", 500)
    filename = digest.replace(":", "_") + ".tar.gz"
    return send_file(
        io.BytesIO(data),
        as_attachment=True,
        download_name=filename,
        mimetype="application/gzip",
    )
