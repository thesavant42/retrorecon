from typing import Any, Dict, List, Optional

from layerslayer.utils import human_readable_size
from layerslayer.client import (
    DockerRegistryClient,
    get_client,
    get_manifest,
    get_manifest_digest,
    list_layer_files as _list_layer_files,
)

from retrorecon import status as status_mod

__all__ = [
    "DockerRegistryClient",
    "get_client",
    "get_manifest",
    "get_manifest_digest",
    "list_layer_files",
    "gather_layers_info",
]


async def list_layer_files(
    image_ref: str,
    digest: str,
    client: Optional[DockerRegistryClient] = None,
) -> List[str]:
    return await _list_layer_files(image_ref, digest, client)


async def _layers_details(
    image_ref: str,
    manifest: Dict[str, Any],
    client: DockerRegistryClient,
) -> List[Dict[str, Any]]:
    layers = manifest.get("layers", [])
    details: List[Dict[str, Any]] = []
    for layer in layers:
        try:
            files = await list_layer_files(image_ref, layer["digest"], client)
        except Exception:
            files = []
        details.append(
            {
                "digest": layer["digest"],
                "size": human_readable_size(layer.get("size", 0) or 0),
                "files": files,
            }
        )
    return details


async def gather_layers_info(image_ref: str) -> List[Dict[str, Any]]:
    status_mod.push_status('layerpeek_start', image_ref)
    async with DockerRegistryClient() as client:
        status_mod.push_status('layerpeek_fetch_manifest', image_ref)
        manifest_index = await get_manifest(image_ref, client=client)
        result: List[Dict[str, Any]] = []
        if manifest_index.get("manifests"):
            platforms = manifest_index["manifests"]
            for m in platforms:
                plat = m.get("platform", {})
                digest = m["digest"]
                status_mod.push_status('layerpeek_fetch_manifest', f"{plat.get('os')}/{plat.get('architecture')}")
                manifest = await get_manifest(image_ref, specific_digest=digest, client=client)
                status_mod.push_status('layerpeek_fetch_layers', digest)
                layers = await _layers_details(image_ref, manifest, client)
                result.append(
                    {
                        "os": plat.get("os"),
                        "architecture": plat.get("architecture"),
                        "layers": layers,
                    }
                )
        else:
            status_mod.push_status('layerpeek_fetch_layers', image_ref)
            layers = await _layers_details(image_ref, manifest_index, client)
            result.append(
                {
                    "os": manifest_index.get("os"),
                    "architecture": manifest_index.get("architecture"),
                    "layers": layers,
                }
            )
        status_mod.push_status('layerpeek_done', image_ref)
        return result
