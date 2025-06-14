import json
from typing import Dict, Any, List

from app import app


def _url_parts(route: str) -> Dict[str, Any]:
    """Return Postman URL object for ``route``."""
    clean = route.lstrip('/')
    return {
        "raw": f"{{{{base_url}}}}{route}",
        "host": ["{{base_url}}"],
        "path": clean.split('/') if clean else []
    }


def build_collection() -> Dict[str, Any]:
    """Generate a Postman collection dictionary from Flask routes."""
    items: List[Dict[str, Any]] = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'static':
            continue
        methods = sorted(m for m in rule.methods if m not in {'HEAD', 'OPTIONS'})
        for method in methods:
            items.append({
                "name": f"{method} {rule.rule}",
                "request": {
                    "method": method,
                    "header": [],
                    "url": _url_parts(rule.rule)
                }
            })
    return {
        "info": {
            "name": "Retrorecon API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": items
    }


if __name__ == '__main__':
    collection = build_collection()
    print(json.dumps(collection, indent=2))
