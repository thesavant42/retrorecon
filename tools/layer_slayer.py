import argparse
import logging
import os
import sys
from typing import List

from layerslayer.fetcher import (
    get_manifest,
    download_layer_blob,
    peek_layer_blob,
    fetch_build_steps,
)
from layerslayer.utils import (
    parse_image_ref,
    human_readable_size,
    load_token,
)


def _setup_logger(log_file: str | None) -> logging.Logger:
    logger = logging.getLogger("layer_slayer")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)
    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore and download individual Docker image layers.")
    parser.add_argument(
        "--target-image", "-t", dest="image_ref",
        help="Image (user/repo:tag) to inspect")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--peek-all", action="store_true",
        help="Peek into all layers and exit")
    group.add_argument(
        "--peek-layer", type=int, metavar="N",
        help="Peek into a specific layer index")
    parser.add_argument(
        "--save-all", action="store_true",
        help="Download all layers and exit")
    parser.add_argument(
        "--log-file", "-l", dest="log_file",
        help="Path to save a complete log of output")
    parser.add_argument(
        "--log-layer", type=int, metavar="N",
        help="Write logs for one layer to a separate file (requires --log-file)")
    return parser.parse_args()


def _select_manifest(image_ref: str, token: str | None):
    result = get_manifest(image_ref, token)
    if isinstance(result, tuple):
        manifest_index, token = result
    else:
        manifest_index = result
    if manifest_index.get("manifests"):
        digest = manifest_index["manifests"][0]["digest"]
        result = get_manifest(image_ref, token, specific_digest=digest)
        if isinstance(result, tuple):
            manifest, _ = result
        else:
            manifest = result
    else:
        manifest = manifest_index
    return manifest, token


def main() -> None:
    args = parse_args()
    if args.log_layer is not None and not args.log_file:
        print("--log-layer requires --log-file", file=sys.stderr)
        raise SystemExit(2)
    logger = _setup_logger(args.log_file)

    image_ref = args.image_ref or "moby/buildkit:latest"
    token = load_token("token.txt")
    manifest, token = _select_manifest(image_ref, token)
    layers: List[dict] = manifest["layers"]

    if args.peek_layer is not None:
        if args.peek_layer < 0 or args.peek_layer >= len(layers):
            logger.error(
                "Invalid layer index %s (0-%d)", args.peek_layer, len(layers) - 1)
            raise SystemExit(1)

    logger.info("Build steps:")
    steps = fetch_build_steps(image_ref, manifest["config"]["digest"], token)
    for i, step in enumerate(steps):
        logger.info(" [%d] %s", i, step)

    def process_layer(idx: int, layer: dict) -> None:
        extra_handler = None
        if args.log_layer is not None and args.log_layer == idx:
            root, ext = os.path.splitext(args.log_file)
            fname = f"{root}.layer{idx}{ext or '.log'}"
            extra_handler = logging.FileHandler(fname, encoding='utf-8')
            extra_handler.setFormatter(logger.handlers[0].formatter)
            logger.addHandler(extra_handler)
        logger.info("\n⦿ Layer [%d] %s", idx, layer['digest'])
        peek_layer_blob(image_ref, layer['digest'], token)
        if extra_handler:
            logger.removeHandler(extra_handler)
            extra_handler.close()

    if args.peek_all or args.peek_layer is not None:
        target_indices = range(len(layers)) if args.peek_all else [args.peek_layer]
        for idx in target_indices:
            process_layer(idx, layers[idx])
        return

    if args.save_all:
        for idx, layer in enumerate(layers):
            logger.info("Downloading Layer [%d] %s", idx, layer['digest'])
            download_layer_blob(image_ref, layer['digest'], layer['size'], token)
        return

    logger.info("Layers:")
    for idx, layer in enumerate(layers):
        size = human_readable_size(layer['size'])
        logger.info(" [%d] %s - %s", idx, layer['digest'], size)


if __name__ == '__main__':
    main()
