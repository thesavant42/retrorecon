from flask import Blueprint, request, jsonify, send_file
import io
import asyncio
from aiohttp import ClientError

from ..docker_layers import gather_layers_info, get_client
from ..layerslayer_utils import parse_image_ref, registry_base_url

bp = Blueprint('docker', __name__)


@bp.route('/docker_layers', methods=['GET'])
def docker_layers_route():
    image = request.args.get('image')
    if not image:
        return jsonify({'error': 'missing_image'}), 400
    try:
        data = asyncio.run(gather_layers_info(image))
    except asyncio.TimeoutError:
        return jsonify({'error': 'timeout'}), 504
    except ClientError as exc:
        return jsonify({'error': 'client_error', 'details': str(exc)}), 502
    except Exception as exc:  # pragma: no cover - unexpected
        return jsonify({'error': 'server_error', 'details': str(exc)}), 500
    for plat in data:
        for layer in plat['layers']:
            layer['download'] = (
                request.url_root.rstrip('/')
                + '/download_layer?image='
                + image
                + '&digest='
                + layer['digest']
            )
    return jsonify(data)


@bp.route('/download_layer', methods=['GET'])
def download_layer_route():
    image = request.args.get('image')
    digest = request.args.get('digest')
    if not image or not digest:
        return ('', 400)
    user, repo, _ = parse_image_ref(image)
    url = f"{registry_base_url(user, repo)}/blobs/{digest}"
    data = asyncio.run(get_client().fetch_bytes(url, user, repo))
    filename = digest.replace(':', '_') + '.tar.gz'
    return send_file(io.BytesIO(data), as_attachment=True, download_name=filename, mimetype='application/gzip')
