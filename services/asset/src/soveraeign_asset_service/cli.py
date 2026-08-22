from __future__ import annotations

import argparse
import json
from .core import AssetService


def main() -> None:
    parser = argparse.ArgumentParser(prog="soveraeign-asset")
    parser.add_argument("--root", default=".soveraeign-asset")
    sub = parser.add_subparsers(dest="command", required=True)
    ingest = sub.add_parser("ingest")
    ingest.add_argument("path")
    ingest.add_argument("--label", required=True)
    ingest.add_argument("--actor", default="human")
    search = sub.add_parser("search")
    search.add_argument("query")
    sub.add_parser("rebuild")
    sub.add_parser("receipts")
    args = parser.parse_args()
    service = AssetService(args.root)
    try:
        if args.command == "ingest":
            result = service.ingest(args.path, args.label, args.actor)
        elif args.command == "search":
            result = service.search(args.query)
        elif args.command == "rebuild":
            result = service.rebuild_projections()
        else:
            result = service.receipts()
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        service.close()


if __name__ == "__main__":
    main()
