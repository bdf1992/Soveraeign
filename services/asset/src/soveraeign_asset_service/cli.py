"""Local command binding for the asset service.

A refusal leaves the process with exit code 2 and prints the declared refusal
code, so a caller can tell a refused act from a crash without parsing prose.
`grant` is a bootstrap command over `authority.grant`, which no manifest
declares while the permits seam is open (OPEN-SEAMS S14, and the same seam that
already covers `search` and `receipts`).
"""

from __future__ import annotations

import argparse
import json
import sys

from .authority import AuthorityRefused
from .core import AssetService
from .librarian import render
from .organization import OrganizationRefused


def build_parser() -> argparse.ArgumentParser:
    """Every command this binding reaches."""
    parser = argparse.ArgumentParser(prog="soveraeign-asset")
    parser.add_argument("--root", default=".soveraeign-asset")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="capture a payload as a version of an asset")
    ingest.add_argument("path")
    ingest.add_argument("--label", required=True)
    ingest.add_argument("--actor", default="human")

    search = sub.add_parser("search", help="assets whose projected text contains a query")
    search.add_argument("query")
    sub.add_parser("rebuild", help="derive the search and graph projections again")
    sub.add_parser("drift", help="name every projected row that disagrees with the ledger")
    sub.add_parser("receipts", help="every receipt in write order")

    grant = sub.add_parser("grant", help="issue a live grant (bootstrap; see OPEN-SEAMS S14)")
    grant.add_argument("--actor", required=True)
    grant.add_argument("--capability", required=True)
    grant.add_argument("--scope", default="*")
    grant.add_argument("--issuer", default="human")

    declare_type = sub.add_parser("declare-type", help="declare a collection type and its schema")
    declare_type.add_argument("type_id")
    declare_type.add_argument("--label", required=True)
    declare_type.add_argument("--spec", required=True, help="path to the JSON spec")
    declare_type.add_argument("--actor", default="human")
    sub.add_parser("types", help="every declared collection type")

    declare = sub.add_parser("declare-collection", help="open a collection of a declared type")
    declare.add_argument("--type", dest="type_id", required=True)
    declare.add_argument("--label", required=True)
    declare.add_argument("--actor", default="human")
    sub.add_parser("collections", help="every collection with its live member count")

    read = sub.add_parser("collection", help="one collection, its type, and its members")
    read.add_argument("collection_id")

    add = sub.add_parser("add-member", help="file an asset into a collection")
    add.add_argument("collection_id")
    add.add_argument("asset_id")
    add.add_argument("--actor", default="human")

    remove = sub.add_parser("remove-member", help="counter a membership; the filing stays")
    remove.add_argument("membership_id")
    remove.add_argument("--actor", default="human")
    remove.add_argument("--reason", required=True)

    conformance = sub.add_parser("conformance", help="judge every collection against its type")
    conformance.add_argument("--markdown", action="store_true")
    return parser


def dispatch(service: AssetService, args: argparse.Namespace) -> object:
    """Run one command against an open service and return what to print."""
    if args.command == "ingest":
        return service.ingest(args.path, args.label, args.actor)
    if args.command == "search":
        return service.search(args.query)
    if args.command == "rebuild":
        return service.rebuild_projections()
    if args.command == "drift":
        return service.projection_drift()
    if args.command == "receipts":
        return service.receipts()
    if args.command == "grant":
        return {"grant_id": service.grant(args.issuer, args.actor, args.capability, args.scope)}
    if args.command == "declare-type":
        with open(args.spec, encoding="utf-8") as handle:
            spec = json.load(handle)
        return {"receipt_id": service.organization.declare_type(
            args.type_id, args.label, spec, args.actor)}
    if args.command == "types":
        return service.organization.types()
    if args.command == "declare-collection":
        return service.organization.declare_collection(args.type_id, args.label, args.actor)
    if args.command == "collections":
        return service.organization.collections()
    if args.command == "collection":
        declared = [entry for entry in service.organization.collections()
                    if entry["collection_id"] == args.collection_id]
        return {"collection": declared[0] if declared else None,
                "members": service.organization.members(args.collection_id),
                "conformance": service.librarian.conformance(args.collection_id)}
    if args.command == "add-member":
        return service.organization.add_member(args.collection_id, args.asset_id, args.actor)
    if args.command == "remove-member":
        return {"receipt_id": service.organization.remove_member(
            args.membership_id, args.actor, args.reason)}
    return service.library_report()


def main(argv: list[str] | None = None) -> int:
    """Parse, dispatch, print. Returns the process exit code."""
    args = build_parser().parse_args(argv)
    service = AssetService(args.root)
    try:
        result = dispatch(service, args)
    except OrganizationRefused as refused:
        print(json.dumps({"refused": refused.code}, indent=2))
        return 2
    except AuthorityRefused as refused:
        print(json.dumps({"refused": "AUTHORITY_REFUSED", "detail": str(refused)}, indent=2))
        return 2
    finally:
        service.close()
    if args.command == "conformance" and args.markdown:
        print(render(result), end="")
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
