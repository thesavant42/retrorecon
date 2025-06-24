# Dynamic schema registration for demo pages
from __future__ import annotations

from flask import render_template
import app
from .dynamic_render import SchemaRegistry


def register_demo_schemas(registry: SchemaRegistry) -> None:
    """Register demo page schemas."""

    registry.register(
        "static_html",
        {
            "required": ["html"],
            "content": [
                {"html_field": "html"}
            ],
        },
    )

    def _index_html() -> str:
        return app.index()

    registry.register(
        "demo_index",
        {"callable": _index_html},
    )

    def _subdom_html() -> str:
        return render_template("subdomonster.html", initial_data=[])

    registry.register(
        "demo_subdomonster",
        {"callable": _subdom_html},
    )

    def _shot_html() -> str:
        return render_template("screenshotter.html")

    registry.register(
        "demo_screenshotter",
        {"callable": _shot_html},
    )

    def _about_html() -> str:
        credits = [
            "the folks referenced in the README",
            "dagdotdev / original registry explorer project",
            "the shupandhack Discord",
        ]
        return render_template("help_about.html", version=app.APP_VERSION, credits=credits)

    registry.register(
        "demo_about",
        {"callable": _about_html},
    )
