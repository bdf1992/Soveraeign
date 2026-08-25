"""Print what the product ground and canon read, one intention at a time.

`scripts/sov_canon.py` owns the judgement - whether the records are admissible - and this
module owns the readings: walking one ground claim, promise or journey down to its
crossings, listing how far the node gets on each promise, viewing one set of usage records
through every intention that contains it, and saying which recorded facts the state has
moved under.

Nothing here judges anything. A reading with every crossing reachable is a reading of what
the node can do, never of what it has done.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json

from sovkernel import attribution
from sovkernel import canon as canon_module
from sovkernel import ground as ground_module

ROOT = Path(__file__).resolve().parents[2]

CANON_PATH = ROOT / "contracts" / "product-canon.json"
GROUND_PATH = ROOT / "contracts" / "product-ground.json"
MAP_PATH = ROOT / "contracts" / "fixtures" / "capability-map.reference.json"

MARKS = {canon_module.REACHABLE: "reachable",
         canon_module.DECLARED: "declared, not reachable",
         canon_module.MISSING: "MISSING"}


def _load(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _print_journey(reading: dict[str, Any], indent: str = "") -> None:
    counts = reading["counts"]
    walk = "walkable today" if reading["walkable"] else "not walkable"
    print(f"{indent}{reading['journey_id']}  {reading['title']}")
    print(f"{indent}  {reading['participant']:<16} serves {', '.join(reading['serves'])}")
    for state in reading["crossings"]:
        mark = MARKS[state["state"]]
        if state["state"] == canon_module.MISSING:
            print(f"{indent}    {state['crossing']:<34} {mark}")
            print(f"{indent}      {state['because']}")
        else:
            carried = ", ".join(state.get("transports") or []) or "-"
            print(f"{indent}    {state['crossing']:<34} {mark:<24} {carried}")
    print(f"{indent}  {counts[canon_module.REACHABLE]} reachable, "
          f"{counts[canon_module.DECLARED]} declared, "
          f"{counts[canon_module.MISSING]} missing - {walk}\n")


def _trace_ground(canon: dict[str, Any], ground: dict[str, Any],
                  capability_map: dict[str, Any], target: str) -> int:
    claim = next((c for c in ground["claims"] if c["ground_id"] == target), None)
    if claim is None:
        print(f"no ground claim {target}")
        return 1
    print(f"\n{claim['ground_id']}\n  {claim['statement']}\n")
    print(f"  if false: {claim['if_false']}\n")
    carried = [p for p in canon["promises"] if target in p["derives_from"]]
    for promise in carried:
        reading = canon_module.promise_reading(canon, capability_map, promise["promise_id"])
        totals = reading["totals"]
        print(f"  {promise['promise_id']:<12} {promise['source']:<28} "
              f"{totals[canon_module.REACHABLE]:>3} reachable, "
              f"{totals[canon_module.DECLARED]:>3} declared, "
              f"{totals[canon_module.MISSING]:>3} missing")
    print(f"\n  carried by {len(carried)} promise(s). A ground claim is not reachable or "
          f"unreachable;\n  it is what the promises below it are for.")
    return 0


def command_trace(args: argparse.Namespace) -> int:
    """Walk one ground claim, promise or journey down to the crossings it needs."""
    canon = _load(CANON_PATH)
    ground = _load(GROUND_PATH)
    capability_map = _load(MAP_PATH)
    target = args.identifier.upper()
    if target.startswith("GROUND-"):
        return _trace_ground(canon, ground, capability_map, target)
    if target.startswith("JOURNEY-"):
        journey = next((j for j in canon["journeys"] if j["journey_id"] == target), None)
        if journey is None:
            print(f"no journey {target}")
            return 1
        print(f"\n{journey['need']}\n")
        _print_journey(canon_module.journey_reading(journey, capability_map))
        return 0
    if not target.startswith("PROMISE-"):
        print("name a GROUND-nnn, a PROMISE-nn or a JOURNEY-nn")
        return 1
    if target not in {p["promise_id"] for p in canon["promises"]}:
        retired = {e["id"]: e for e in canon["retired"]}
        if target in retired:
            entry = retired[target]
            print(f"\n{target} was retired in {entry['retired_in']}.\n"
                  f"  {entry['because']}\n")
            return 0
        print(f"no promise {target}")
        return 1
    reading = canon_module.promise_reading(canon, capability_map, target)
    print(f"\n{reading['promise_id']}  [{reading['phase']}]  {reading['source']}")
    print(f"  {reading['statement']}\n")
    print(f"  derives from {', '.join(reading['derives_from'])}")
    if reading["composes"]:
        print(f"  composes {', '.join(reading['composes'])}")
    print()
    for journey in reading["journeys"]:
        _print_journey(journey, indent="  ")
    totals = reading["totals"]
    print(f"  ACROSS {len(reading['journeys'])} journeys and "
          f"{reading['distinct_crossings']} distinct crossings "
          f"({reading['journey_appearances']} appearances, counted once): "
          f"{totals[canon_module.REACHABLE]} reachable, "
          f"{totals[canon_module.DECLARED]} declared and unreachable, "
          f"{totals[canon_module.MISSING]} missing")
    return 0


def command_promises(args: argparse.Namespace) -> int:
    """One line per promise: where it came from, and how far the node gets on it today."""
    canon = _load(CANON_PATH)
    capability_map = _load(MAP_PATH)
    print(f"{'promise':<12} {'phase':<8} {'source':<28} {'reach':>5} {'decl':>5} "
          f"{'miss':>5}  ground")
    for promise in canon["promises"]:
        reading = canon_module.promise_reading(canon, capability_map, promise["promise_id"])
        totals = reading["totals"]
        print(f"{promise['promise_id']:<12} {promise['phase']:<8} {promise['source']:<28} "
              f"{totals[canon_module.REACHABLE]:>5} {totals[canon_module.DECLARED]:>5} "
              f"{totals[canon_module.MISSING]:>5}  "
              f"{', '.join(c.replace('GROUND-', '') for c in promise['derives_from'])}")
    for entry in canon["retired"]:
        print(f"{entry['id']:<12} RETIRED in {entry['retired_in']}")
    return 0


def command_ground(args: argparse.Namespace) -> int:
    """One line per ground claim: which promises carry it, and how they arrived."""
    canon = _load(CANON_PATH)
    ground = _load(GROUND_PATH)
    print(f"{ground['epoch']} / {ground['rendering']}   {len(ground['claims'])} claims\n")
    for row in ground_module.ground_reading(canon, ground):
        print(f"{row['ground_id']}  {row['statement'].split('.')[0][:88]}")
        print(f"             carried by {', '.join(row['promises'])}")
    return 0


def command_rollup(args: argparse.Namespace) -> int:
    """Show one set of usage records through every intention that contains it."""
    canon = _load(CANON_PATH)
    units = _load(Path(args.usage))
    result = attribution.rollup(canon, units["units"])
    dims = sorted(result["measured"])
    print(f"\n{result['unit_count']} usage record(s), "
          f"{result['attributed']} attributable to a journey")
    print("MEASURED ONCE: " + ", ".join(
        f"{result['measured'][d]:g} {d}" for d in dims) + "\n")
    for level in attribution.LEVELS:
        gap = attribution.overlap(result, level)
        print(f"  viewed through {level}:")
        for identifier, bucket in sorted(result["views"][level].items()):
            spent = ", ".join(f"{bucket['consumed'].get(d, 0):g} {d}" for d in dims)
            print(f"    {identifier:<34} {len(bucket['units']):>2} unit(s)  {spent}")
        over = ", ".join(f"{gap[d]:g} {d}" for d in dims if gap[d])
        print(f"    summing these views would invent {over or 'nothing'}\n")
    if result["unattributed"]:
        print(f"  unattributed: {', '.join(result['unattributed'])} - the capability they "
              f"served is crossed by no journey")
    return 0


def command_facts(args: argparse.Namespace) -> int:
    """Read the example state facts, and say which of them the state has moved under.

    Staleness is computed here, never stored. A fact records the capability revision it
    was read from; comparing that to the live map is what makes it stale, and the fact
    itself is left exactly as it was.
    """
    facts = _load(Path(args.facts))["facts"]
    current = _load(MAP_PATH)["input_state_digest"]
    print()
    print(f"capability revision now {current[:16]}")
    print()
    for fact in facts:
        pinned = fact["state_inputs"]["capability_revision"]
        stale = pinned != current
        mark = "STALE" if stale else fact["evidential_status"]
        print(f"  {fact['fact_id']:<28} {mark:<10} read at {pinned[:16]}")
        print(f"    {fact['claim']}")
        print(f"    ground {', '.join(fact['ground'])}"
              f"  promise {', '.join(fact.get('promise', []))}"
              f"  journey {', '.join(fact.get('journey', []))}")
        if stale:
            successor = fact.get("superseded_by", "nothing")
            print(f"    the state it rested on moved; superseded by {successor}. Its "
                  f"ground, promise and journey did not move.")
        print()
    return 0
