"""Custom Swagger UI blueprint using Retrorecon styling."""

import json
import os
from flask import Blueprint, current_app, request, send_from_directory
from .dynamic import dynamic_template
import flask_swagger_ui

SWAGGER_URL = '/swagger'
API_URL = '/static/openapi.yaml'

DIST_DIR = os.path.join(os.path.dirname(flask_swagger_ui.__file__), "dist")

bp = Blueprint("swagger_ui", __name__, url_prefix=SWAGGER_URL)


@bp.route("/swagger-dark.css")
def swagger_dark_css():
    """Serve the custom Swagger UI dark theme."""
    return current_app.send_static_file("swagger-dark.css")

_config = {
    "app_name": "Retrorecon Swagger",
    "dom_id": "#swagger-ui",
    "url": API_URL,
    "layout": "StandaloneLayout",
    "deepLinking": True,
    "displayRequestDuration": True,
    "tryItOutEnabled": True,
}


@bp.route("/")
@bp.route("/<path:path>")
def show(path: str | None = None):
    """Serve the Swagger UI with Retrorecon styling."""
    if not path or path == "index.html":
        if not _config.get("oauth2RedirectUrl"):
            _config["oauth2RedirectUrl"] = os.path.join(request.base_url, "oauth2-redirect.html")
        fields = {
            "base_url": SWAGGER_URL,
            "app_name": _config.get("app_name", "Swagger UI"),
            "config_json": json.dumps({k: v for k, v in _config.items() if k != "app_name"}),
        }
        return dynamic_template("swaggerui.html", **fields)
    return send_from_directory(DIST_DIR, path)
