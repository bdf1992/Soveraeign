#!/usr/bin/env python3
"""Read the product ground and canon, and trace an intention down to what is reachable.

`GROUND.md` says what product this is; `CANON.md` says what it undertakes and to whom.
The two JSON records beside them carry the identifiers, and `check` refuses if the prose
and the records disagree, if a promise derives from a ground claim that is not there, if a
ground claim no promise carries, or if a promise is canonical only because something was
built that way.

`trace` walks one ground claim, promise or journey down to its crossings. `rollup` takes a
file of usage records and shows one expenditure through every intention that contains it,
without counting it more than once.

Every read is local. Nothing here serves an endpoint, settles a standing, or grants
anything: a promise with every crossing reachable is a promise the node can keep, not one
it has kept.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import canon as canon_module  # noqa: E402
from sovkernel import ground as ground_module  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402
from sovcanon import readings  # noqa: E402

CANON_PATH = ROOT / "contracts" / "product-canon.json"
CANON_SCHEMA = ROOT / "contracts" / "product-canon.schema.json"
GROUND_PATH = ROOT / "contracts" / "product-ground.json"
GROUND_SCHEMA = ROOT / "contracts" / "product-ground.schema.json"
MAP_PATH = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"
CANON_WORDING = ROOT / "CANON.md"
GROUND_WORDING = ROOT / "GROUND.md"


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def wording_defects(canon: dict[str, Any], wording: str) -> list[str]:
    """Every identifier in the record must appear in the document that owns its wording.

    Two places holding one fact drift unless something checks them. This is the same
    shape `decisions/0037` settled for the two ticket readers: agreement by check rather
    than by coincidence.
    """
    found = []
    for promise in canon["promises"]:
        if promise["promise_id"] not in wording:
            found.append(f"UNWORDED_PROMISE: {promise['promise_id']} is declared in the "
                         f"record and absent from {canon['wording_owned_by']}")
    for journey in canon["journeys"]:
        if journey["journey_id"] not in wording:
            found.append(f"UNWORDED_JOURNEY: {journey['journey_id']} is declared in the "
                         f"record and absent from {canon['wording_owned_by']}")
    for key in ("epoch", "revision", "rendering"):
        if canon[key] not in wording:
            found.append(f"UNWORDED_{key.upper()}: {canon[key]} is absent from "
                         f"{canon['wording_owned_by']}")
    for entry in canon["retired"]:
        if entry["id"] not in wording:
            found.append(f"UNWORDED_RETIREMENT: {entry['id']} was retired and "
                         f"{canon['wording_owned_by']} does not say so; a reader "
                         f"following an old attribution has to be able to find out")
    return found


def all_defects(canon: dict[str, Any], ground: dict[str, Any],
                capability_map: dict[str, Any]) -> tuple[list[str], list[str]]:
    """Schema defects and join defects, over both records at once."""
    schema = ([f"canon: {d}" for d in validate(canon, _load(CANON_SCHEMA))]
              + [f"ground: {d}" for d in validate(ground, _load(GROUND_SCHEMA))])
    recorded = (ROOT / "STATUS.yaml").read_bytes().decode("utf-8")
    joins = (ground_module.ground_defects(ground)
             + ground_module.acceptance_defects(ground, "GROUND", recorded)
             + ground_module.acceptance_defects(canon, "CANON", recorded)
             + ground_module.rendering_defects(canon, "CANON")
             + ground_module.join_defects(canon, ground)
             + ground_module.wording_defects(
                 ground, GROUND_WORDING.read_bytes().decode("utf-8"))
             + canon_module.defects(canon, capability_map)
             + wording_defects(canon, CANON_WORDING.read_bytes().decode("utf-8")))
    return schema, joins


def command_check(args: argparse.Namespace) -> int:
    """Judge ground and canon against their schemas, each other, and their own wording."""
    canon = _load(CANON_PATH)
    ground = _load(GROUND_PATH)
    schema, joins = all_defects(canon, ground, _load(MAP_PATH))
    for defect in schema:
        print(f"CONTRACT: {defect}")
    for defect in joins:
        print(f"DEFECT: {defect}")
    if schema or joins:
        print(f"\nFAIL: {len(schema) + len(joins)} defect(s)")
        return 1
    print(f"PASS: {ground['epoch']} / {ground['rendering']} declares "
          f"{len(ground['claims'])} ground claims; {canon['rendering']} declares "
          f"{len(canon['participants'])} participants, {len(canon['promises'])} promises "
          f"and {len(canon['journeys'])} journeys")
    print("      every promise derives from a declared ground claim, every ground claim "
          "is carried by a promise,")
    print("      every join resolves, and every identifier is worded in its own document")
    print(f"Standing: ground {ground['status']}, canon {canon['status']}. Acceptance "
          f"fixes what these mean;")
    print("      it is not evidence that the node keeps any of them, and it grants nothing.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sov_canon", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    checker = sub.add_parser("check", help="judge ground, canon, their joins and wording")
    checker.set_defaults(handler=command_check)

    tracer = sub.add_parser("trace", help="walk one intention down to its crossings")
    tracer.add_argument("identifier", help="GROUND-nnn, PROMISE-nn or JOURNEY-nn")
    tracer.set_defaults(handler=readings.command_trace)

    lister = sub.add_parser("promises", help="how far the node gets on each promise")
    lister.set_defaults(handler=readings.command_promises)

    grounder = sub.add_parser("ground", help="which promises carry each ground claim")
    grounder.set_defaults(handler=readings.command_ground)

    roller = sub.add_parser("rollup", help="view usage through every intention, counted once")
    roller.add_argument("usage", help="path to a usage record file")
    roller.set_defaults(handler=readings.command_rollup)

    facts = sub.add_parser("facts", help="which recorded facts the state has moved under")
    facts.add_argument("facts", nargs="?",
                       default=str(ROOT / "contracts" / "fixtures" /
                                   "state-fact.example.json"),
                       help="path to a state-fact file")
    facts.set_defaults(handler=readings.command_facts)

    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
