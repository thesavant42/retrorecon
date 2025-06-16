"""Utility helpers from the layerslayer project."""

import os
from typing import Optional


def parse_image_ref(image_ref: str):
    if ":" in image_ref:
        repo, tag = image_ref.split(":", 1)
    else:
        repo = image_ref
        tag = "latest"
    if "/" in repo:
        user, repo = repo.split("/", 1)
    else:
        user = "library"
    return user, repo, tag


def registry_base_url(user: str, repo: str) -> str:
    return f"https://registry-1.docker.io/v2/{user}/{repo}"


def human_readable_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def load_token(filename: str) -> Optional[str]:
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return f.read().strip()
    return None


def save_token(token: str, filename: str = "token.txt") -> None:
    with open(filename, "w") as f:
        f.write(token)
