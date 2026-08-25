#!/usr/bin/env python3
"""Read and rebuild the capability map: which office answers which operation, and how.

``contracts/capability-offices.json`` is the policy this reads; the map under
``contracts/fixtures/capability-map.reference.json`` is the projection it rebuilds.
Nothing here serves an endpoint or grants anything. ``show`` answers "what doors
exist and which of them are open"; ``check`` answers "does the checked-in map still
tell the truth about the manifests".
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import receipt_events  # noqa: E402
from sovkernel.capability_map import build, is_stale, map_defects  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

CONTRACTS = ROOT / "contracts"
TABLE_PATH = CONTRACTS / "capability-offices.json"
SCHEMA_PATH = CONTRACTS / "capability-map.schema.json"
MAP_PATH = CONTRACTS / "fixtures" / "capability-map.reference.json"
PHASE = "FOUNDING"


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _manifest_paths() -> list[Path]:
    return sorted((ROOT / "services").glob("*/contracts/service.json"))


def _manifests() -> dict[str, dict[str, Any]]:
    loaded: dict[str, dict[str, Any]] = {}
    for path in _manifest_paths():
        manifest = _load(path)
        loaded[manifest["service_id"]] = manifest
    return loaded


def _derived_from() -> list[str]:
    addresses = [path.relative_to(ROOT).as_posix() for path in _manifest_paths()]
    addresses.append(TABLE_PATH.relative_to(ROOT).as_posix())
    return addresses


def _rebuild() -> dict[str, Any]:
    return build(_manifests(), _load(TABLE_PATH), phase=PHASE, derived_from=_derived_from())


def _open_endpoints(row: dict[str, Any]) -> list[str]:
    return [endpoint["transport"] for endpoint in row["endpoints"]
            if endpoint["activation"] == "ACTIVE"]


def command_build(args: argparse.Namespace) -> int:
    """Rebuild the map from the manifests and the office table."""
    document = _rebuild()
    defects = validate(document, _load(SCHEMA_PATH)) + map_defects(
        document, _manifests(), _load(TABLE_PATH))
    if defects:
        for defect in defects:
            print(f"DEFECT: {defect}")
        print(f"\nREFUSED: the rebuilt map carries {len(defects)} defect(s); nothing written")
        return 1
    if args.dry_run:
        print(json.dumps(document, indent=2))
        return 0
    MAP_PATH.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"BUILT: {len(document['capabilities'])} capabilities -> "
          f"{MAP_PATH.relative_to(ROOT).as_posix()}")
    print(f"input_state_digest {document['input_state_digest'][:16]}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    """Validate the checked-in map against its contract and its inputs."""
    document = _load(MAP_PATH)
    manifests, table = _manifests(), _load(TABLE_PATH)
    schema_defects = validate(document, _load(SCHEMA_PATH))
    semantic_defects = map_defects(document, manifests, table)
    stale = is_stale(document, manifests, table)
    for defect in schema_defects:
        print(f"CONTRACT: {defect}")
    for defect in semantic_defects:
        print(f"DEFECT: {defect}")
    if stale:
        print("STALE: the manifests or the office table have moved past this build; "
              "run `sov_capability.py build`")
    if schema_defects or semantic_defects or stale:
        return 1
    print(f"PASS: {len(document['capabilities'])} capabilities, no defect, not stale")
    print("Standing note: the map is a projection at PROPOSED standing; it witnesses "
          "no endpoint and grants no authority.")
    return 0


def command_show(args: argparse.Namespace) -> int:
    """Print the capability map, optionally narrowed to one office, service, or transport."""
    document = _load(MAP_PATH)
    rows = document["capabilities"]
    if args.office:
        rows = [row for row in rows if row["office"] == args.office]
    if args.service:
        rows = [row for row in rows if row["service_id"] == args.service]
    if args.open_only:
        rows = [row for row in rows if _open_endpoints(row)]
    if not rows:
        print("no capability matches that filter")
        return 0
    width = max(len(row["capability_id"]) for row in rows)
    office = None
    for row in sorted(rows, key=lambda r: (r["office"], r["counter"], r["capability_id"])):
        heading = f"{row['office']} / {row['counter']}"
        if heading != office:
            office = heading
            print(f"\n== {heading}")
        served = ", ".join(_open_endpoints(row)) or "-"
        print(f"  {row['capability_id']:<{width}}  {row['required_authority']:<24} "
              f"{row['service_standing']:<9} {'/'.join(row['actor_kinds']):<12} open: {served}")
    print(f"\n{len(rows)} capabilities shown of {len(document['capabilities'])}")
    return 0


def command_offices(args: argparse.Namespace) -> int:
    """Summarise the offices and what each transport is allowed to be."""
    document = _load(MAP_PATH)
    table = _load(TABLE_PATH)
    counts: dict[str, int] = {}
    for row in document["capabilities"]:
        counts[f"{row['office']}/{row['counter']}"] = counts.get(
            f"{row['office']}/{row['counter']}", 0) + 1
    for office in ("FRONT", "BACK"):
        print(f"== {office} OFFICE")
        for counter, description in table["counters"][office].items():
            print(f"  {counter:<18} {counts.get(f'{office}/{counter}', 0):>3}  {description}")
    print("\n== TRANSPORTS")
    for transport, policy in table["transport_policy"].items():
        flags = []
        if policy["operator_facing"]:
            flags.append("operator-facing")
        if policy["external"]:
            flags.append("external")
        refused = transport in table["external_transports_refused_in_phase"]
        state = "REFUSED in this phase" if refused else "admissible"
        print(f"  {transport:<12} {state:<22} {', '.join(flags) or 'internal'}")
    return 0


def command_events(args: argparse.Namespace) -> int:
    """Judge the receipt event names each service emits against the map they must resolve to.

    A receipt names the operation it is a receipt for. When that name is not the
    operation's capability identifier, the receipt cannot be joined to the row saying
    what the operation costs and where it is reachable, so the node records what
    happened without recording what it was doing.
    """
    document = _load(MAP_PATH)
    defects, harvested = receipt_events.run(ROOT, document, _manifests())
    capability_ids = {row["capability_id"] for row in document["capabilities"]}
    total = 0
    for service_id, events in sorted(harvested.items()):
        resolved = sorted(event for event in events if event in capability_ids)
        excused = sorted(event for event in events if event not in capability_ids)
        total += len(events)
        print(f"{service_id:<10} {len(events):>3} emitted   "
              f"{len(resolved):>3} resolve to a capability   "
              f"{len(excused):>3} declared as no operation")
        if args.verbose:
            for event in resolved:
                print(f"    {event:<32} {events[event][0]}")
            for event in excused:
                print(f"    {event:<32} {events[event][0]}   (undeclared_events)")
    if defects:
        print()
        for defect in defects:
            print(f"FAIL: {defect}")
        return 1
    print(f"\nPASS: {total} emitted receipt events across {len(harvested)} services; "
          f"every one resolves to a declared capability or to a stated reason it does not")
    print("Standing note: agreement between names. It witnesses no operation and grants "
          "nothing.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_capability", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    events = sub.add_parser("events", help="judge emitted receipt events against the map")
    events.add_argument("--verbose", action="store_true", help="list every event and its site")
    events.set_defaults(handler=command_events)

    builder = sub.add_parser("build", help="rebuild the map from the manifests and the table")
    builder.add_argument("--dry-run", action="store_true", help="print instead of writing")
    builder.set_defaults(handler=command_build)

    checker = sub.add_parser("check", help="validate the checked-in map and its freshness")
    checker.set_defaults(handler=command_check)

    shower = sub.add_parser("show", help="print the capability map")
    shower.add_argument("--office", choices=["FRONT", "BACK"])
    shower.add_argument("--service")
    shower.add_argument("--open-only", action="store_true",
                        help="only capabilities served on some transport today")
    shower.set_defaults(handler=command_show)

    offices = sub.add_parser("offices", help="summarise offices, counters, and transports")
    offices.set_defaults(handler=command_offices)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
