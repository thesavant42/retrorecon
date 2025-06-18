from __future__ import annotations

import json
from typing import Any, Dict

from markupsafe import Markup, escape

from layerslayer.utils import parse_image_ref, human_readable_size


_SPEC_LINKS = {
    "application/vnd.docker.distribution.manifest.v2+json": "https://github.com/opencontainers/image-spec/blob/main/manifest.md",
    "application/vnd.docker.image.rootfs.diff.tar.gzip": "https://github.com/opencontainers/image-spec/blob/main/layer.md",
    "application/vnd.docker.container.image.v1+json": "https://github.com/opencontainers/image-spec/blob/main/config.md",
}


def _link_media_type(media_type: str) -> str:
    url = _SPEC_LINKS.get(media_type)
    text = escape(media_type)
    if url:
        return f'<a class="mt" href="{url}">{text}</a>'
    return text


def _render_layer(layer: Dict[str, Any], repo: str) -> str:
    media_type = str(layer.get("mediaType", ""))
    digest = str(layer.get("digest", ""))
    size = int(layer.get("size", 0) or 0)
    digest_link = (
        f'<a href="/fs/{repo}@{digest}?mt={escape(media_type)}&size={size}">{escape(digest)}</a>'
    )
    size_link = (
        f'<a href="/size/{repo}@{digest}?mt={escape(media_type)}&size={size}">' \
        f'<span title="{human_readable_size(size)}">{size}</span></a>'
    )
    parts = [
        '{',
        f'<div class="indent">"mediaType": "{_link_media_type(media_type)}",</div>',
        f'<div class="indent">"digest": "{digest_link}",</div>',
        f'<div class="indent">"size": {size_link}</div>',
        '}',
    ]
    return "<br>".join(parts)


def _render_obj(obj: Any, repo: str) -> str:
    if isinstance(obj, dict):
        lines = ['{']
        items = list(obj.items())
        for idx, (k, v) in enumerate(items):
            comma = ',' if idx < len(items) - 1 else ''
            if k == 'layers' and isinstance(v, list):
                layer_lines = ['[']
                for i, layer in enumerate(v):
                    layer_html = _render_layer(layer, repo)
                    layer_lines.append(f'<div class="indent">{layer_html}</div>' + (' ,' if i < len(v)-1 else ''))
                layer_lines.append(']')
                value_html = "<br>".join(layer_lines)
            elif k == 'mediaType' and isinstance(v, str):
                value_html = f'"{_link_media_type(v)}"'
            else:
                value_html = _render_obj(v, repo)
            lines.append(f'<div class="indent">"{escape(k)}": {value_html}{comma}</div>')
        lines.append('}')
        return "<br>".join(lines)
    if isinstance(obj, list):
        lines = ['[']
        for i, item in enumerate(obj):
            comma = ',' if i < len(obj) - 1 else ''
            lines.append(f'<div class="indent">{_render_obj(item, repo)}{comma}</div>')
        lines.append(']')
        return "<br>".join(lines)
    if isinstance(obj, str):
        return f'"{escape(obj)}"'
    return escape(json.dumps(obj))


def manifest_links(manifest: Dict[str, Any], image: str) -> Markup:
    """Return HTML for ``manifest`` with layer digests and sizes hyperlinked."""
    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"
    html = _render_obj(manifest, repo_full)
    return Markup(html)

