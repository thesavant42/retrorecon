from flask import Blueprint, request, jsonify
from ..dynamic_render import AssetRegistry, SchemaRegistry, HTMLGenerator, render_from_payload

bp = Blueprint('dynamic', __name__)

asset_registry = AssetRegistry()
schema_registry = SchemaRegistry()
html_generator = HTMLGenerator(asset_registry)


@bp.route('/api/render', methods=['POST'])
def api_render():
    """Render HTML from a JSON payload."""
    if not request.is_json:
        return jsonify({'error': 'invalid_payload'}), 400
    payload = request.get_json()
    try:
        html = render_from_payload(payload, schema_registry, html_generator)
    except (KeyError, ValueError) as exc:
        return jsonify({'error': str(exc)}), 400
    return html

