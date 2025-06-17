from flask import Blueprint, request, jsonify
import asyncio
from aiohttp import ClientError

from layerslayer.utils import parse_image_ref
from .. import registry_explorer as rex

bp = Blueprint('registry', __name__)


@bp.route('/registry_explorer', methods=['GET'])
def registry_explorer_route():
    image = request.args.get('image')
    method = request.args.get('method', 'extension')
    if not image:
        return jsonify({'error': 'missing_image'}), 400

    async def _gather_and_digest() -> tuple[list, str | None]:
        return await asyncio.gather(
            rex.gather_image_info_with_backend(image, method),
            rex.get_manifest_digest(image),
        )

    try:
        data, digest = asyncio.run(_gather_and_digest())
    except asyncio.TimeoutError:
        return jsonify({'error': 'timeout'}), 504
    except ClientError as exc:
        return jsonify({'error': 'client_error', 'details': str(exc)}), 502
    except Exception as exc:
        return jsonify({'error': 'server_error', 'details': str(exc)}), 500

    owner, repo, tag = parse_image_ref(image)
    result = {
        'owner': owner,
        'repo': repo,
        'tag': tag,
        'manifest': digest,
        'method': method,
        'platforms': data,
    }
    return jsonify(result)

