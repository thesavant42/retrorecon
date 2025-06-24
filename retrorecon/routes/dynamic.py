from flask import Blueprint, request, jsonify, render_template
from ..dynamic_render import AssetRegistry, SchemaRegistry, HTMLGenerator, render_from_payload
from ..dynamic_schemas import register_demo_schemas
import app

bp = Blueprint('dynamic', __name__)

asset_registry = AssetRegistry()
schema_registry = SchemaRegistry()
html_generator = HTMLGenerator(asset_registry)
register_demo_schemas(schema_registry)


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


@bp.route('/demo/<name>', methods=['GET'])
def demo_dynamic(name: str):
    """Return dynamic HTML for demo pages."""
    if name == 'index':
        html = app.index()
    elif name == 'subdomonster':
        html = render_template('subdomonster.html', initial_data=[])
    elif name == 'screenshotter':
        html = render_template('screenshotter.html')
    elif name == 'about':
        credits = [
            'the folks referenced in the README',
            'dagdotdev / original registry explorer project',
            'the shupandhack Discord',
        ]
        html = render_template('help_about.html', version=app.APP_VERSION, credits=credits)
    else:
        return ('', 404)

    payload = {
        'schema': 'static_html',
        'data': {'html': html},
    }
    return render_from_payload(payload, schema_registry, html_generator)

