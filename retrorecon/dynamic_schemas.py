# Dynamic schema registration for built-in pages
from __future__ import annotations

import json
import app
from .dynamic_render import SchemaRegistry


def register_demo_schemas(registry: SchemaRegistry) -> None:
    """Register base schemas used for dynamic pages."""

    registry.register(
        "static_html",
        {
            "required": ["html"],
            "content": [
                {"html_field": "html"}
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
                                    "attrs": {"type": "button", "class": "btn", "id": "screenshot-toggle-btn"},
                                    "text": "Toggle Thumbs",
                                },
                                {
                                    "tag": "button",
                                    "attrs": {"type": "button", "class": "btn", "id": "screenshot-close-btn"},
                                    "text": "Close",
                                },
                            ],
                        },
                        {"tag": "div", "attrs": {"id": "screenshot-table", "class": "mt-05"}},
                        {"tag": "textarea", "attrs": {"id": "screenshot-log", "class": "form-input debug-output mt-05", "rows": "6", "readonly": ""}},
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
