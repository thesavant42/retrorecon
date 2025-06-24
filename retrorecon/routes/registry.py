from flask import Blueprint, request, jsonify, render_template
import app
import asyncio
from aiohttp import ClientError

from layerslayer.utils import parse_image_ref
from .. import registry_explorer as rex

bp = Blueprint('registry', __name__)


@bp.route('/registry_viewer', methods=['GET'])
def registry_viewer_page():
    return render_template('registry_explorer.html')


@bp.route('/tools/registry_viewer', methods=['GET'])
def registry_viewer_full_page():
    return app.index()


@bp.route('/registry_explorer', methods=['GET'])
def registry_explorer_route():
    image = request.args.get('image')
    files_flag = request.args.get('files', 'false').lower() in {'1', 'true', 'yes'}
    methods_param = request.args.get('methods')
    if methods_param:
        methods = [m.strip() for m in methods_param.split(',') if m.strip()]
    else:
        methods = [request.args.get('method', 'extension')]
    if not image:
        return jsonify({'error': 'missing_image'}), 400

    addr_type = rex.detect_address_type(image)

    async def _gather():
        if len(methods) == 1:
            return await rex.gather_image_info_with_backend(
                image, methods[0], fetch_files=files_flag
            )
        return await rex.gather_image_info_multi(
            image, methods, fetch_files=files_flag
        )

    async def _digest() -> str | None:
        return await rex.get_manifest_digest(image)

    try:
        data = asyncio.run(_gather())
        digest = asyncio.run(_digest())
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
        'addressType': addr_type,
    }
    if len(methods) == 1:
        result['method'] = methods[0]
        result['platforms'] = data
    else:
        result['methods'] = methods
        result['results'] = data
    return jsonify(result)


@bp.route('/registry_table', methods=['GET'])
def registry_table_route():
    """Return manifest contents as a hierarchical table."""
    image = request.args.get('image')
    if not image:
        return jsonify({'error': 'missing_image'}), 400
    addr_type = rex.detect_address_type(image)

    async def _gather():
        return await rex.gather_image_info_with_backend(image, 'extension', fetch_files=True)

    async def _digest():
        return await rex.get_manifest_digest(image)

    try:
        data = asyncio.run(_gather())
        digest = asyncio.run(_digest())
    except asyncio.TimeoutError:
        return jsonify({'error': 'timeout'}), 504
    except ClientError as exc:
        return jsonify({'error': 'client_error', 'details': str(exc)}), 502
    except Exception as exc:
        return jsonify({'error': 'server_error', 'details': str(exc)}), 500

    table = rex.manifest_to_table(data)
    owner, repo, tag = parse_image_ref(image)
    return jsonify({
        'owner': owner,
        'repo': repo,
        'tag': tag,
        'manifest': digest,
        'addressType': addr_type,
        'table': table,
    })
