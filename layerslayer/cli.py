import argparse
import asyncio
import json
from .client import gather_layers_info


def main():
    parser = argparse.ArgumentParser(description="Inspect Docker image layers")
    parser.add_argument("image", help="image reference, e.g. user/repo:tag")
    args = parser.parse_args()
    data = asyncio.run(gather_layers_info(args.image))
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
