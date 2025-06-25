# Minimal dynamic rendering utilities
from __future__ import annotations

from typing import Dict, List
from pathlib import Path
import json
from bs4 import BeautifulSoup
from jsonschema import validate as jsonschema_validate, ValidationError


class AssetRegistry:
    """Registry for CSS and JS assets used during dynamic rendering."""

    def __init__(self) -> None:
        self._assets: List[Dict[str, object]] = []
        self.loaded = False

    def register(self, path: str, asset_type: str, order: int = 0) -> None:
        if asset_type not in {"css", "js"}:
            raise ValueError("asset_type must be 'css' or 'js'")
        for asset in self._assets:
            if asset["path"] == path and asset["type"] == asset_type:
                asset["order"] = order
                break
        else:
            self._assets.append({"path": path, "type": asset_type, "order": order})
        self._assets.sort(key=lambda a: a["order"])

    def load_from_records(self, records: List[Dict[str, object]]) -> None:
        """Load assets from database records."""
        self._assets = []
        for r in records:
            self.register(r["path"], r.get("asset_type", r.get("type", "")), r.get("load_order", r.get("order", 0)))
        self.loaded = True

    def for_render(self) -> Dict[str, List[str]]:
        css = [a["path"] for a in self._assets if a["type"] == "css"]
        js = [a["path"] for a in self._assets if a["type"] == "js"]
        return {"css": css, "js": js}

    @property
    def assets(self) -> List[Dict[str, object]]:
        return list(self._assets)


class SchemaRegistry:
    """Registry of content schemas with simple validation."""

    def __init__(self) -> None:
        self._schemas: Dict[str, Dict[str, object]] = {}

    def register_from_file(self, path: str | Path, name: str | None = None) -> None:
        """Load a schema from a JSON file and register it."""
        p = Path(path)
        with p.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)
        self.register(name or p.stem, schema)

    def load_from_dir(self, directory: str | Path) -> None:
        """Load and register all ``.json`` schemas in a directory."""
        d = Path(directory)
        if not d.exists():
            return
        for f in d.glob("*.json"):
            self.register_from_file(f)

    def register(self, name: str, schema: Dict[str, object]) -> None:
        self._schemas[name] = schema

    def get(self, name: str) -> Dict[str, object]:
        return self._schemas[name]

    def validate(self, name: str, data: Dict[str, object]) -> None:
        schema = self._schemas.get(name)
        if not schema:
            raise KeyError(name)
        validation_schema = schema.get("validation") if "validation" in schema else schema
        try:
            jsonschema_validate(instance=data, schema=validation_schema)
        except ValidationError as exc:
            raise ValueError(str(exc)) from exc


class HTMLGenerator:
    """Generate HTML content from a simple schema."""

    def __init__(self, asset_registry: AssetRegistry | None = None) -> None:
        self.asset_registry = asset_registry or AssetRegistry()

    def render(self, schema: Dict[str, object], data: Dict[str, object]) -> str:
        soup = BeautifulSoup("", "html.parser")
        root = soup.new_tag("div", **{"class": "retrorecon-root"})
        soup.append(root)

        def add_nodes(parent, nodes):
            for node in nodes:
                if "html_field" in node:
                    html_val = data.get(node["html_field"], "")
                    frag = BeautifulSoup(html_val, "html.parser")
                    for child in frag.contents:
                        parent.append(child)
                    continue
                tag = node.get("tag")
                if not tag:
                    continue
                el = soup.new_tag(tag)
                attrs = node.get("attrs", {})
                for k, v in attrs.items():
                    el.attrs[k] = v
                text_key = node.get("text")
                if text_key is not None:
                    # If the key exists in the provided data use that value,
                    # otherwise treat the text attribute as a literal string.
                    value = data.get(text_key, text_key)
                    el.string = str(value)
                if node.get("children"):
                    add_nodes(el, node["children"])
                parent.append(el)

        add_nodes(root, schema.get("content", []))

        assets = self.asset_registry.for_render()
        for css in assets["css"]:
            link = soup.new_tag("link", rel="stylesheet", href=css)
            soup.head.insert(0, link) if soup.head else soup.insert(0, link)
        for js in assets["js"]:
            script = soup.new_tag("script", src=js)
            soup.append(script)
        return str(soup)


def render_from_payload(payload: Dict[str, object], registry: SchemaRegistry, generator: HTMLGenerator) -> str:
    name = payload.get("schema")
    data = payload.get("data", {})
    if not isinstance(name, str):
        raise ValueError("schema field required")
    schema = registry.get(name)
    registry.validate(name, data)
    return generator.render(schema, data)

