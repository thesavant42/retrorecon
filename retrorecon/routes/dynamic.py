from flask import Blueprint, request, jsonify, render_template, abort
from jinja2 import TemplateNotFound
import json
from markupsafe import escape
from ..dynamic_render import AssetRegistry, SchemaRegistry, HTMLGenerator, render_from_payload
from ..dynamic_schemas import register_demo_schemas
from pathlib import Path
from ..asset_utils import list_assets
from retrorecon import subdomain_utils

import app

bp = Blueprint('dynamic', __name__, url_prefix='/dynamic')

asset_registry = AssetRegistry()
schema_registry = SchemaRegistry()
html_generator = HTMLGenerator(asset_registry)
register_demo_schemas(schema_registry)
schema_registry.load_from_dir(Path(app.app.root_path) / "schemas")


def dynamic_template(template: str, **context) -> str:
    """Render *template* via the dynamic renderer unless legacy mode is requested."""
    use_legacy = context.pop("use_legacy", False)
    if request.args.get("legacy") == "1":
        use_legacy = True
    try:
        html = render_template(template, **context)
    except TemplateNotFound:
        abort(404)
    if use_legacy:
        return html
    payload = {"schema": "static_html", "data": {"html": html}}
    return render_from_payload(payload, schema_registry, html_generator)


@bp.before_app_request
def _load_assets() -> None:
    if not asset_registry.loaded and app.app.config.get('DATABASE'):
        try:
            records = list_assets()
            asset_registry.load_from_records(records)
        except Exception:
            pass


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



