# utils.py
# 🛡️ Layerslayer utilities

import os

def parse_image_ref(image_ref):
    """Return ``(user, repo, tag)`` for an image reference.

    This helper understands registry domains like ``ghcr.io`` and also handles
    references that omit a repository component such as ``registry.k8s.io``.
    ``tag`` defaults to ``"latest"`` if absent.
    """

    tag = "latest"
    ref = image_ref

    # Split tag if it appears after the last slash
    if ":" in image_ref and image_ref.rfind(":") > image_ref.rfind("/"):
        ref, tag = image_ref.rsplit(":", 1)

    if "/" in ref:
        first, remainder = ref.split("/", 1)
        if "." in first or ":" in first or first == "localhost":
            # ``first`` is actually a registry domain
            user = first
            repo = remainder
        else:
            user = first
            repo = remainder
    else:
        if "." in ref or ":" in ref or ref == "localhost":
            # Domain only with no repository path
            user = ref
            repo = ""
        else:
            user = "library"
            repo = ref

    return user, repo, tag

def registry_base_url(user: str, repo: str) -> str:
    """Return the base registry URL for ``user`` and ``repo``."""
    if "." in user or ":" in user or user == "localhost":
        # ``user`` already includes a registry domain like ``ghcr.io``.
        # Treat it as the full hostname and do not prepend Docker Hub.
        return f"https://{user}/v2/{repo}"
    return f"https://registry-1.docker.io/v2/{user}/{repo}"


def guess_manifest_media_type(image_ref_or_host: str) -> str:
    """Return expected manifest media type for ``image_ref_or_host``.

    The logic mirrors the registry-aware parser described in issue #607.
    ``image_ref_or_host`` may be an image reference like ``gcr.io/foo/bar`` or a
    bare hostname such as ``docker.io``.
    """
    host = image_ref_or_host
    if "/" in image_ref_or_host:
        first = image_ref_or_host.split("/", 1)[0]
        if "." in first or ":" in first or first == "localhost":
            host = first
        else:
            host = "docker.io"
    elif "." not in host and ":" not in host and host != "localhost":
        # bare repository name like "ubuntu" implies Docker Hub
        host = "docker.io"
    if host in {"docker.io", "index.docker.io"}:
        return "application/vnd.docker.distribution.manifest.v2+json"
    if host.endswith("gcr.io") or host.endswith("pkg.dev") or host.endswith("registry.k8s.io"):
        return "application/vnd.oci.image.manifest.v1+json"
    if host.endswith("ecr.aws") or host.endswith("quay.io"):
        return "application/vnd.docker.distribution.manifest.v2+json"
    # fallback for unknown registries
    return "application/vnd.oci.image.manifest.v1+json"

def auth_headers(token=None):
    headers = {"Accept": "application/vnd.docker.distribution.manifest.v2+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def human_readable_size(size):
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def load_token(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read().strip()
    return None

def save_token(token, filename="token.txt"):
    with open(filename, "w") as f:
        f.write(token)

