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
    digest_link = f'<a href="/fs/{repo}@{digest}">{escape(digest)}</a>'
    size_link = (
        f'<a href="/size/{repo}@{digest}?mt={escape(media_type)}&size={size}">' 
        f'<span title="{human_readable_size(size)}">{size}</span></a>'
    )
    parts = [
        '{',
        f'<span class="indent">"mediaType": "{_link_media_type(media_type)}",</span>',
        f'<span class="indent">"digest": "{digest_link}",</span>',
        f'<span class="indent">"size": {size_link}</span>',
        '}',
    ]
    return "\n".join(parts)


def _render_manifest_entry(entry: Dict[str, Any], repo: str, manifest_digest: str = "", image_ref: str | None = None) -> str:
    media_type = str(entry.get("mediaType", ""))
    digest = str(entry.get("digest", ""))
    size = int(entry.get("size", 0) or 0)
    digest_link = f'<a href="/?image={repo}@{digest}">{escape(digest)}</a>'
    size_link = (
        f'<a href="/size/{repo}@{digest}?mt={escape(media_type)}&size={size}">' 
        f'<span title="{human_readable_size(size)}">{size}</span></a>'
    )
    parts = ["{"]
    parts.append(
        f'<span class="indent">"mediaType": "{_link_media_type(media_type)}",</span>'
    )
    parts.append(f'<span class="indent">"digest": "{digest_link}",</span>')
    parts.append(f'<span class="indent">"size": {size_link}</span>')
    platform = entry.get("platform")
    if platform is not None:
        parts.append(
            f'<span class="indent">"platform": {_render_obj(platform, repo, manifest_digest, image_ref)}</span>'
        )
    parts.append("}")
    return "\n".join(parts)


def _render_obj(obj: Any, repo: str, manifest_digest: str = "", image_ref: str | None = None) -> str:
    if isinstance(obj, dict):
        lines = ['{']
        items = list(obj.items())
        for idx, (k, v) in enumerate(items):
            comma = ',' if idx < len(items) - 1 else ''
            if k == 'layers' and isinstance(v, list):
                key_html = (
                    f'<a href="/layers/{image_ref}@{manifest_digest}/">layers</a>'
                    if manifest_digest and image_ref
                    else escape(k)
                )
                layer_lines = ['[']
                for i, layer in enumerate(v):
                    layer_html = _render_layer(layer, repo)
                    suffix = ',' if i < len(v)-1 else ''
                    layer_lines.append(f'<span class="indent">{layer_html}{suffix}</span>')
                layer_lines.append(']')
                value_html = "\n".join(layer_lines)
            elif k == 'manifests' and isinstance(v, list):
                man_lines = ['[']
                for i, m in enumerate(v):
                    man_html = _render_manifest_entry(m, repo, manifest_digest, image_ref)
                    suffix = ',' if i < len(v)-1 else ''
                    man_lines.append(f'<span class="indent">{man_html}{suffix}</span>')
                man_lines.append(']')
                value_html = "\n".join(man_lines)
            elif k == 'mediaType' and isinstance(v, str):
                value_html = f'"{_link_media_type(v)}"'
            else:
                value_html = _render_obj(v, repo, manifest_digest, image_ref)
            if k == 'layers' and isinstance(v, list) and manifest_digest:
                lines.append(f'<span class="indent">"{key_html}": {value_html}{comma}</span>')
            else:
                lines.append(f'<span class="indent">"{escape(k)}": {value_html}{comma}</span>')
        lines.append('}')
        return "\n".join(lines)
    if isinstance(obj, list):
        lines = ['[']
        for i, item in enumerate(obj):
            comma = ',' if i < len(obj) - 1 else ''
            lines.append(f'<span class="indent">{_render_obj(item, repo, manifest_digest, image_ref)}{comma}</span>')
        lines.append(']')
        return "\n".join(lines)
    if isinstance(obj, str):
        return f'"{escape(obj)}"'
    return escape(json.dumps(obj))


def manifest_links(manifest: Dict[str, Any], image: str, digest: str = "") -> Markup:
    """Return HTML for ``manifest`` with layer digests and sizes hyperlinked."""
    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"
    html = _render_obj(manifest, repo_full, digest, image)
    return Markup(html)

