"""Read and judge the declared service surface.

``check`` judges every manifest against the kernel refusal vocabulary, the kernel transition
table, PRD.md, and the manifest's own declarations. ``endpoints`` prints the logical address of
every declared operation. ``crud`` reports which append-preserving CRUD verbs each service
covers. Nothing here serves an endpoint, opens a transport, or grants anything.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import manifests

STANDING_NOTE = ("Standing note: a manifest is a declared surface at its own standing; declaring "
                 "an operation neither builds it nor opens a transport to it.")


def _check(args: argparse.Namespace) -> int:
    total, findings = manifests.check_all()
    services = len(manifests.manifest_paths())
    if findings:
        for finding in findings:
            print(f"DEFECT: {finding}")
        print(f"FAIL: {len(findings)} defects across {services} service manifests")
        return 1
    print(f"PASS: {services} service manifests, {total} declared operations, no defect")
    print(STANDING_NOTE)
    return 0


def _endpoints(args: argparse.Namespace) -> int:
    rows = manifests.endpoints()
    if args.service:
        rows = [row for row in rows if row["service_id"] == args.service]
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    current = None
    for row in rows:
        if row["service_id"] != current:
            current = row["service_id"]
            print(f"\n== {current}")
        requirement = row["requirement"] or "-"
        print(f"  {row['logical_endpoint']:44} {row['crud']:10} {row['standing']:9} "
              f"{requirement:9} {row['commit']}")
    print(f"\n{len(rows)} logical endpoints")
    print(STANDING_NOTE)
    return 0


def _crud(args: argparse.Namespace) -> int:
    rows = manifests.crud_coverage()
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    verbs = ("CREATE", "READ", "SUPERSEDE", "COUNTER", "REBUILD")
    print(f"{'service':12}{'standing':10}{'ops':>4}{'built':>7}   " + "  ".join(f"{v:9}" for v in verbs))
    for row in rows:
        cells = []
        for verb in verbs:
            names = row["verbs"].get(verb, [])
            cells.append(f"{len(names):<9}" if names else f"{'-':<9}")
        print(f"{row['service_id']:12}{row['standing']:10}{row['operations']:>4}{row['built']:>7}   "
              + "  ".join(cells))
    print("\nCREATE appends. READ derives without writing. SUPERSEDE adds a later version and "
          "keeps the earlier one.\nCOUNTER adds a counter-record and erases nothing. REBUILD "
          "recomputes a projection only.")
    print(STANDING_NOTE)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_service", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="judge every service manifest")
    check.set_defaults(handler=_check)

    endpoints = sub.add_parser("endpoints", help="print every declared logical endpoint")
    endpoints.add_argument("--service", help="limit to one service id")
    endpoints.add_argument("--json", action="store_true", help="emit JSON")
    endpoints.set_defaults(handler=_endpoints)

    crud = sub.add_parser("crud", help="report CRUD coverage per service")
    crud.add_argument("--json", action="store_true", help="emit JSON")
    crud.set_defaults(handler=_crud)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
