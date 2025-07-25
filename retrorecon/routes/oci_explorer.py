from flask import Blueprint, request, jsonify
from .dynamic import dynamic_template
import app
import asyncio
from aiohttp import ClientError
from aiohttp import ClientConnectorCertificateError

from layerslayer.utils import parse_image_ref
from .. import registry_explorer as rex

bp = Blueprint('oci_explorer', __name__)


@bp.route('/oci_explorer', methods=['GET'])
def oci_explorer_page():
    """Serve the OCI Explorer overlay."""
    return dynamic_template('registry_explorer.html')


@bp.route('/tools/oci_explorer', methods=['GET'])
def oci_explorer_full_page():
    """Serve the main dashboard so the overlay can open on load."""
    return app.index()


@bp.route('/oci_explorer_api', methods=['GET'])
def oci_explorer_route():
    image = request.args.get('image')
    files_flag = request.args.get('files', 'false').lower() in {'1', 'true', 'yes'}
    if not image:
        return jsonify({'error': 'missing_image'}), 400

    addr_type = rex.detect_address_type(image)

    async def _gather(method: str):
        return await rex.gather_image_info_with_backend(
            image, method, fetch_files=files_flag, insecure=True
        )

    async def _digest() -> str | None:
        return await rex.get_manifest_digest(image, insecure=True)

    try:
        try:
            data = asyncio.run(_gather('extension'))
            method_used = 'extension'
        except Exception:
            data = asyncio.run(_gather('layerslayer'))
            method_used = 'layerslayer'
        digest = asyncio.run(_digest())
    except asyncio.TimeoutError:
        return jsonify({'error': 'timeout'}), 504
    except ClientError as exc:
        return jsonify({'error': 'client_error', 'details': str(exc)}), 502
    except Exception as exc:
        return jsonify({'error': 'server_error', 'details': str(exc)}), 500

    owner, repo, tag = parse_image_ref(image)
    return jsonify({
        'owner': owner,
        'repo': repo,
        'tag': tag,
        'manifest': digest,
        'addressType': addr_type,
        'insecure': True,
        'method': method_used,
        'platforms': data,
    })


@bp.route('/oci_table', methods=['GET'])
def oci_table_route():
    """Return manifest contents as a hierarchical table."""
    image = request.args.get('image')
    insecure_flag = request.args.get('insecure', 'false').lower() in {'1', 'true', 'yes'}
    if not image:
        return jsonify({'error': 'missing_image'}), 400
    addr_type = rex.detect_address_type(image)

    async def _gather(insecure: bool):
        return await rex.gather_image_info_with_backend(
            image, 'extension', fetch_files=True, insecure=insecure
        )

    async def _digest(insecure: bool):
        return await rex.get_manifest_digest(image, insecure=insecure)

    try:
        data = asyncio.run(_gather(insecure_flag))
        digest = asyncio.run(_digest(insecure_flag))
    except asyncio.TimeoutError:
        return jsonify({'error': 'timeout'}), 504
    except ClientConnectorCertificateError:
        if not insecure_flag:
            try:
                data = asyncio.run(_gather(True))
                digest = asyncio.run(_digest(True))
                insecure_flag = True
            except Exception as exc:
                return jsonify({'error': 'client_error', 'details': str(exc)}), 502
        else:
            return jsonify({'error': 'client_error', 'details': 'ssl_error'}), 502
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
        'insecure': insecure_flag,
        'table': table,
    })
