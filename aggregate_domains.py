"""Aggregate hostnames into hierarchical counts."""
import argparse
import json
import sys
from typing import Dict, Any

from retrorecon import domain_sort


def print_tree(tree: Dict[str, Any], indent: int = 0) -> None:
    """Print ``tree`` in an indented format sorted by count."""
    for label, data in sorted(
        tree.items(), key=lambda kv: kv[1].get("_count", 0) if isinstance(kv[1], dict) else 0, reverse=True
    ):
        if not isinstance(data, dict):
            continue
        count = data.get("_count", 0)
        print("  " * indent + f"{label} ({count})")
        print_tree(data.get("_children", {}), indent + 1)


def flatten_tree(tree: Dict[str, Any]):
    """Return ``(domain, count)`` tuples from ``tree``."""
    return domain_sort.flatten_tree(tree)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate subdomains from URLs or hostnames")
    parser.add_argument("input", nargs="?", help="File with one URL or host per line (default: stdin)")
    parser.add_argument("--top-k", type=int, dest="top_k", help="Show only the top K paths")
    parser.add_argument("--output", choices=["tree", "json", "flat"], default="tree", help="Output format")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.input:
        with open(args.input, "r", encoding="utf-8") as fh:
            lines = [l.strip() for l in fh if l.strip()]
    else:
        lines = [l.strip() for l in sys.stdin if l.strip()]

    hosts = domain_sort.extract_hosts(lines)
    tree = domain_sort.aggregate_hosts(hosts)

    if args.output == "json":
        print(json.dumps(tree, indent=2))
        return

    if args.output == "flat":
        entries = flatten_tree(tree)
        entries.sort(key=lambda x: x[1], reverse=True)
        if args.top_k:
            entries = entries[: args.top_k]
        for domain, count in entries:
            print(f"{domain} {count}")
        return

    # default tree output
    print_tree(tree)


if __name__ == "__main__":
    main()
