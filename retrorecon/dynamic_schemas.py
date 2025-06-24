# Dynamic schema registration for demo pages
from __future__ import annotations

from flask import render_template
import json
from markupsafe import escape
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

    registry.register(
        "subdomonster_page",
        {
            "required": ["init_script"],
            "content": [
                {
                    "tag": "div",
                    "attrs": {"id": "subdomonster-overlay", "class": "notes-overlay hidden"},
                    "children": [
                        {
                            "tag": "div",
                            "attrs": {"class": "mb-05"},
                            "children": [
                                {
                                    "tag": "input",
                                    "attrs": {
                                        "type": "text",
                                        "id": "subdomonster-domain",
                                        "class": "form-input mr-05",
                                        "placeholder": "example.com",
                                    },
                                },
                                {
                                    "tag": "select",
                                    "attrs": {"id": "subdomonster-source", "class": "form-select mr-05"},
                                    "children": [
                                        {"tag": "option", "attrs": {"value": "crtsh", "selected": True}, "text": "crt.sh"},
                                        {"tag": "option", "attrs": {"value": "virustotal"}, "text": "VirusTotal"},
                                        {"tag": "option", "attrs": {"value": "local"}, "text": "Local"},
                                    ],
                                },
                                {
                                    "tag": "input",
                                    "attrs": {
                                        "type": "text",
                                        "id": "subdomonster-api-key",
                                        "class": "form-input mr-05 hidden",
                                        "placeholder": "API key",
                                    },
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "subdomonster-fetch-btn"},
                                    "text": "Fetch",
                                },
                                {
                                    "tag": "input",
                                    "attrs": {
                                        "type": "text",
                                        "id": "subdomonster-search",
                                        "class": "form-input mr-05",
                                        "placeholder": "search",
                                    },
                                },
                                {
                                    "tag": "select",
                                    "attrs": {"id": "subdom-export-formats", "class": "form-select mr-05"},
                                    "children": [
                                        {"tag": "option", "attrs": {"value": "", "selected": True}, "text": "Export as..."},
                                        {"tag": "option", "attrs": {"value": "md"}, "text": "Markdown"},
                                        {"tag": "option", "attrs": {"value": "csv"}, "text": "CSV"},
                                        {"tag": "option", "attrs": {"value": "json"}, "text": "JSON"},
                                    ],
                                },
                                {
                                    "tag": "form",
                                    "attrs": {
                                        "id": "subdom-export-form",
                                        "class": "hidden",
                                        "action": "/export_subdomains",
                                        "method": "GET",
                                        "target": "_blank",
                                    },
                                    "children": [
                                        {
                                            "tag": "input",
                                            "attrs": {"type": "hidden", "name": "domain", "id": "subdom-export-domain"},
                                        },
                                        {
                                            "tag": "input",
                                            "attrs": {"type": "hidden", "name": "format", "id": "subdom-export-format"},
                                        },
                                        {
                                            "tag": "input",
                                            "attrs": {"type": "hidden", "name": "q", "id": "subdom-export-q"},
                                        },
                                    ],
                                },
                                {
                                    "tag": "select",
                                    "attrs": {"id": "subdom-select-mode", "class": "form-select mr-05"},
                                    "children": [
                                        {"tag": "option", "attrs": {"value": "", "selected": True}, "text": "Select..."},
                                        {"tag": "option", "attrs": {"value": "page"}, "text": "Select Page"},
                                        {"tag": "option", "attrs": {"value": "all"}, "text": "Select All Matching"},
                                        {"tag": "option", "attrs": {"value": "none"}, "text": "Select None"},
                                    ],
                                },
                                {
                                    "tag": "input",
                                    "attrs": {
                                        "type": "text",
                                        "id": "subdom-bulk-tag",
                                        "class": "form-input mr-05",
                                        "placeholder": "tag",
                                    },
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "subdom-add-tag-btn"},
                                    "text": "Add Tag",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "subdom-remove-tag-btn"},
                                    "text": "Remove Tag",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "subdom-clear-tags-btn"},
                                    "text": "Clear Tags",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "subdom-delete-btn"},
                                    "text": "Delete Selected",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "subdomonster-close-btn"},
                                    "text": "Close",
                                },
                                {
                                    "tag": "span",
                                    "attrs": {"id": "subdomonster-status", "class": "ml-05"},
                                },
                            ],
                        },
                        {"tag": "div", "attrs": {"id": "subdomonster-table", "class": "mt-05"}},
                        {"tag": "div", "attrs": {"id": "subdomonster-pagination", "class": "mt-05"}},
                        {"html_field": "init_script"},
                    ],
                }
            ],
        },
    )

    registry.register(
        "screenshotter_page",
        {
            "content": [
                {
                    "tag": "div",
                    "attrs": {"id": "screenshot-overlay", "class": "notes-overlay hidden"},
                    "children": [
                        {
                            "tag": "div",
                            "attrs": {"class": "mb-05"},
                            "children": [
                                {
                                    "tag": "input",
                                    "attrs": {
                                        "type": "text",
                                        "id": "screenshot-url",
                                        "class": "form-input mr-05 w-20em",
                                        "placeholder": "https://example.com",
                                    },
                                },
                                {
                                    "tag": "select",
                                    "attrs": {"id": "screenshot-agent", "class": "form-select mr-05"},
                                    "children": [
                                        {"tag": "option", "attrs": {"value": ""}, "text": "Desktop"},
                                        {"tag": "option", "attrs": {"value": "android"}, "text": "Android"},
                                        {"tag": "option", "attrs": {"value": "bot"}, "text": "Search Engine"},
                                    ],
                                },
                                {
                                    "tag": "label",
                                    "attrs": {"class": "mr-05"},
                                    "children": [
                                        {
                                            "tag": "input",
                                            "attrs": {"type": "checkbox", "id": "screenshot-ref", "class": "form-checkbox"},
                                        },
                                        {"text": " Spoof referrer"},
                                    ],
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "screenshot-capture-btn"},
                                    "text": "Capture",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "screenshot-delete-btn"},
                                    "text": "Delete",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "screenshot-close-btn"},
                                    "text": "Close",
                                },
                            ],
                        },
                        {"tag": "div", "attrs": {"id": "screenshot-table", "class": "mt-05"}},
                    ],
                }
            ],
        },
    )

    registry.register(
        "help_about_page",
        {
            "required": ["version", "credits_html"],
            "content": [
                {
                    "tag": "div",
                    "attrs": {"id": "help-about-overlay", "class": "notes-overlay hidden help-overlay"},
                    "children": [
                        {
                            "tag": "div",
                            "attrs": {"class": "d-flex flex-between mb-4px"},
                            "children": [
                                {"tag": "span", "text": "title"},
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "help-about-close-btn"},
                                    "text": "Close",
                                },
                            ],
                        },
                        {
                            "tag": "p",
                            "children": [
                                {
                                    "tag": "a",
                                    "attrs": {
                                        "href": "https://github.com/thesavant42/retrorecon",
                                        "target": "_blank",
                                    },
                                    "text": "Project on GitHub",
                                }
                            ],
                        },
                        {"tag": "p", "text": "version"},
                        {
                            "tag": "div",
                            "attrs": {"class": "credits-scroll"},
                            "children": [
                                {"html_field": "credits_html"}
                            ],
                        },
                    ],
                }
            ],
        },
    )
