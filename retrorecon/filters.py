from __future__ import annotations

import json
import datetime
from typing import Any, Dict

from markupsafe import Markup, escape

from layerslayer.utils import parse_image_ref, human_readable_size


_SPEC_LINKS = {
    "application/vnd.docker.distribution.manifest.v2+json": "https://github.com/opencontainers/image-spec/blob/main/manifest.md",
    "application/vnd.docker.image.rootfs.diff.tar.gzip": "https://github.com/opencontainers/image-spec/blob/main/layer.md",
    "application/vnd.docker.container.image.v1+json": "https://github.com/opencontainers/image-spec/blob/main/config.md",
}


def wb_timestamp(ts: str | None) -> str:
    """Return Wayback timestamp ``ts`` formatted as YYYY-MM-DD HH:MM:SS."""
    if not ts:
        return ""
    try:
        dt = datetime.datetime.strptime(str(ts), "%Y%m%d%H%M%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(ts)


def _link_media_type(media_type: str) -> str:
    url = _SPEC_LINKS.get(media_type)
    text = escape(media_type)
    if url:
        return f'<a class="mt" href="{url}">{text}</a>'
    return text


def _render_layer(layer: Dict[str, Any], repo: str, link_size: bool = True) -> str:
    media_type = str(layer.get("mediaType", ""))
    digest = str(layer.get("digest", ""))
    size = int(layer.get("size", 0) or 0)
    digest_link = f'<a href="/fs/{repo}@{digest}">{escape(digest)}</a>'
    if link_size:
        size_link = (
            f'<a href="/size/{repo}@{digest}?mt={escape(media_type)}&size={size}">'
            f'<span title="{human_readable_size(size)}">{size}</span></a>'
        )
    else:
        size_link = f'<span title="{human_readable_size(size)}">{size}</span>'
    parts = ["{"]
    parts.append(
        f'<span class="indent">"mediaType": "{_link_media_type(media_type)}",</span>'
    )
    parts.append(f'<span class="indent">"digest": "{digest_link}",</span>')
    parts.append(f'<span class="indent">"size": {size_link}</span>')
    annotations = layer.get("annotations")
    if annotations is not None:
        parts.append(
            f'<span class="indent">"annotations": {_render_obj(annotations, repo)}</span>'
        )
    for k, v in layer.items():
        if k in {"mediaType", "digest", "size", "annotations"}:
            continue
        parts.append(
            f'<span class="indent">"{escape(k)}": {_render_obj(v, repo)}</span>'
        )
    parts.append("}")
    return "\n".join(parts)


def _render_manifest_entry(
    entry: Dict[str, Any],
    repo: str,
    manifest_digest: str = "",
    image_ref: str | None = None,
    link_size: bool = True,
) -> str:
    media_type = str(entry.get("mediaType", ""))
    digest = str(entry.get("digest", ""))
    size = int(entry.get("size", 0) or 0)
    digest_link = f'<a href="/image/{repo}@{digest}">{escape(digest)}</a>'
    if link_size:
        size_link = (
            f'<a href="/size/{repo}@{digest}?mt={escape(media_type)}&size={size}">' 
            f'<span title="{human_readable_size(size)}">{size}</span></a>'
        )
    else:
        size_link = f'<span title="{human_readable_size(size)}">{size}</span>'
    parts = ["{"]
    parts.append(
        f'<span class="indent">"mediaType": "{_link_media_type(media_type)}",</span>'
    )
    parts.append(f'<span class="indent">"digest": "{digest_link}",</span>')
    parts.append(f'<span class="indent">"size": {size_link}</span>')
    platform = entry.get("platform")
    if platform is not None:
        parts.append(
            '<span class="indent">"platform": '
            f'{_render_obj(platform, repo, manifest_digest, image_ref)}</span>'
        )
    annotations = entry.get("annotations")
    if annotations is not None:
        parts.append(
            '<span class="indent">"annotations": '
            f'{_render_obj(annotations, repo, manifest_digest, image_ref)}</span>'
        )
    for k, v in entry.items():
        if k in {"mediaType", "digest", "size", "platform", "annotations"}:
            continue
        parts.append(
            f'<span class="indent">"{escape(k)}": '
            f'{_render_obj(v, repo, manifest_digest, image_ref)}</span>'
        )
    parts.append("}")
    return "\n".join(parts)


def _render_obj(
    obj: Any,
    repo: str,
    manifest_digest: str = "",
    image_ref: str | None = None,
    link_size: bool = True,
) -> str:
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
                    layer_html = _render_layer(layer, repo, link_size=link_size)
                    suffix = ',' if i < len(v)-1 else ''
                    layer_lines.append(f'<span class="indent">{layer_html}{suffix}</span>')
                layer_lines.append(']')
                value_html = "\n".join(layer_lines)
            elif k == 'manifests' and isinstance(v, list):
                man_lines = ['[']
                for i, m in enumerate(v):
                    man_html = _render_manifest_entry(
                        m, repo, manifest_digest, image_ref, link_size=link_size
                    )
                    suffix = ',' if i < len(v)-1 else ''
                    man_lines.append(f'<span class="indent">{man_html}{suffix}</span>')
                man_lines.append(']')
                value_html = "\n".join(man_lines)
            elif k == 'mediaType' and isinstance(v, str):
                value_html = f'"{_link_media_type(v)}"'
            else:
                value_html = _render_obj(v, repo, manifest_digest, image_ref, link_size=link_size)
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
            lines.append(
                f'<span class="indent">{_render_obj(item, repo, manifest_digest, image_ref, link_size=link_size)}{comma}</span>'
            )
        lines.append(']')
        return "\n".join(lines)
    if isinstance(obj, str):
        return f'"{escape(obj)}"'
    return escape(json.dumps(obj))


def manifest_links(
    manifest: Dict[str, Any],
    image: str,
    digest: str = "",
    *,
    link_size: bool = True,
) -> Markup:
    """Return HTML for ``manifest`` with layer digests and sizes hyperlinked."""
    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"
    html = _render_obj(manifest, repo_full, digest, image, link_size=link_size)
    return Markup(html)


def oci_obj(obj: Any, repo: str, *, link_size: bool = True) -> Markup:
    """Return HTML representation for arbitrary OCI JSON structures."""
    html = _render_obj(obj, repo, link_size=link_size)
    return Markup(html)


def manifest_table(manifest: Dict[str, Any], image: str) -> Markup:
    """Return HTML tables summarizing ``manifest``.

    The config and layer digests are linked to download routes so users can
    easily fetch individual blobs. If ``manifest`` is a manifest list, each
    entry links to the corresponding image view instead.
    """

    user, repo, _ = parse_image_ref(image)
    repo_full = f"{user}/{repo}"

    def _link_digest(digest: str, download: bool = True) -> str:
        href = (
            f"/download_layer?image={image}&digest={digest}"
            if download
            else f"/image/{repo_full}@{digest}"
        )
        return f'<a class="mt" href="{href}">{escape(digest)}</a>'

    parts: list[str] = []

    # Config overview table
    cfg = manifest.get("config", {})
    cfg_rows = [
        ("schemaVersion", manifest.get("schemaVersion")),
        ("mediaType", manifest.get("mediaType")),
        ("config.digest", cfg.get("digest")),
        ("config.size", cfg.get("size")),
        ("config.mediaType", cfg.get("mediaType")),
    ]
    parts.append(
        '<table class="fs-table"><thead><tr><th>Key</th><th>Value</th></tr></thead><tbody>'
    )
    for key, val in cfg_rows:
        if key.endswith("digest") and val:
            val_html = _link_digest(str(val))
        elif key.endswith("size") and val is not None:
            size_hr = human_readable_size(int(val) if str(val).isdigit() else 0)
            val_html = f'{val} <span class="text-muted">({size_hr})</span>'
        else:
            val_html = escape(str(val)) if val is not None else ""
        parts.append(
            f'<tr><td class="text-mono">{escape(key)}</td><td class="text-mono">{val_html}</td></tr>'
        )
    parts.append("</tbody></table>")

    layers = manifest.get("layers")
    if layers:
        parts.append(
            '<table class="fs-table"><thead><tr><th>#</th><th>Size</th><th>Digest</th><th>Media Type</th><th class="text-center">💾</th><th class="text-center">🔍</th></tr></thead><tbody>'
        )
        for idx, layer in enumerate(layers, 1):
            d = str(layer.get("digest", ""))
            size = layer.get("size", 0)
            mt = str(layer.get("mediaType", ""))
            size_hr = human_readable_size(int(size) if str(size).isdigit() else 0)
            download_link = f'/download_layer?image={image}&digest={d}'
            browse_link = f'/fs/{repo_full}@{d}'
            parts.append(
                f'<tr><td>{idx}</td><td>{size} <span class="text-muted">({size_hr})</span></td>'
                f'<td>{_link_digest(d, False)}</td><td>{escape(mt)}</td>'
                f'<td class="text-center"><a href="{download_link}" title="Download">💾</a></td>'
                f'<td class="text-center"><a href="{browse_link}" title="Browse">🔍</a></td></tr>'
            )
        parts.append("</tbody></table>")
    elif manifest.get("manifests"):
        parts.append(
            '<table class="fs-table"><thead><tr><th>#</th><th>Size</th><th>Digest</th><th>Media Type</th><th>Platform</th></tr></thead><tbody>'
        )
        for idx, entry in enumerate(manifest["manifests"], 1):
            d = str(entry.get("digest", ""))
            size = entry.get("size", 0)
            mt = str(entry.get("mediaType", ""))
            plat = ""
            if entry.get("platform"):
                os_ = entry["platform"].get("os", "")
                arch = entry["platform"].get("architecture", "")
                plat = f"{os_}/{arch}".strip("/")
            size_hr = human_readable_size(int(size) if str(size).isdigit() else 0)
            parts.append(
                f'<tr><td>{idx}</td><td>{size} <span class="text-muted">({size_hr})</span></td><td>{_link_digest(d, False)}</td><td>{escape(mt)}</td><td>{escape(plat)}</td></tr>'
            )
        parts.append("</tbody></table>")

    return Markup("".join(parts))

