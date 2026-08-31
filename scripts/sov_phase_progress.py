#!/usr/bin/env python3
"""Hold the phase gate reading to a floor, so coverage becomes a number that refuses.

`scripts/sov_f2_gate.py` has read the distance between `SPEC.md` and the
conformance corpus since it was written, and returns non-zero whenever the gate
is open. It was never in the check table, so for six days it read 0 of 44 and
nothing refused (`reports/2026-08-27-phase-i-retro.md`, finding 1).

Registering the gate itself would refuse every run until the phase exit is
earned, which teaches a reader to ignore it. This grades the reading against a
recorded floor instead: a fall refuses, because a fall requires an edit to the
corpus or the specification and is attributable to that edit. A stall does not
refuse, for the reason `decisions/0081` removed the wall clock from the exit
code - the participant who lands the commit crossing the ceiling is not the
participant who let the number sit still.

The exclusion list is what keeps the floor honest. Every predicate between the
floor and the total is named with a reason, so raising the floor and closing a
gap are the same act, and a predicate that becomes covered forces its own
exclusion to be deleted.

Every read is local. Nothing here reaches the coordination surface.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import subprocess

import sov_f2_gate
from sov_active_phase_progress import grade_active_phase, phase_record, status_phase


ROOT = Path(__file__).resolve().parents[1]

CONTRACT = "contracts/phase-progress.json"


def _contract() -> dict:
    """The declared floor, exclusions, and refusals."""
    return json.loads((ROOT / CONTRACT).read_bytes().decode("utf-8"))


def commits_since(commit: str) -> int | None:
    """Commits between `commit` and HEAD, or None when it is not in this history.

    Unreachable is the ordinary case here rather than a defect: the repository
    carries several trunks and a floor pinned on one is not an ancestor of
    another.
    """
    try:
        result = subprocess.run(["git", "rev-list", "--count", f"{commit}..HEAD"],
                                cwd=ROOT, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def covered_ids(report: dict) -> set[str]:
    """Predicate ids the reading credits with both polarities."""
    open_ids = {row["id"] for row in report["open"]}
    spec_text = sov_f2_gate._text(sov_f2_gate.SPEC)
    stated = {predicate["id"] for predicate in sov_f2_gate.normative_predicates(spec_text)}
    return stated - open_ids


def grade(report: dict, contract: dict) -> list[dict]:
    """Every refusal the declared contract fires against this gate reading."""
    defects: list[dict] = []
    floor = contract["floor"]

    if floor["total"] > report["predicates_total"]:
        defects.append({
            "code": "FLOOR_ABOVE_CEILING",
            "detail": f"floor is {floor['total']} and SPEC.md states "
                      f"{report['predicates_total']} predicates",
        })

    if report["predicates_covered"] < floor["total"]:
        defects.append({
            "code": "PREDICATE_REGRESSION",
            "detail": f"the gate reads {report['predicates_covered']} covered and the "
                      f"floor is {floor['total']}",
        })
    for family, expected in floor["by_family"].items():
        counts = report["by_family"].get(family)
        if counts is None:
            continue
        covered = counts["total"] - counts["open"]
        if covered < expected:
            defects.append({
                "code": "PREDICATE_REGRESSION",
                "detail": f"{family} reads {covered} covered and its floor is {expected}",
            })

    for predicate_id in report["orphan_declarations"]:
        defects.append({
            "code": "UNKNOWN_PREDICATE",
            "detail": f"{predicate_id} is declared by a control and absent from SPEC.md",
        })

    excused = {entry["predicate"] for entry in contract["uncovered_on_purpose"]}
    open_ids = {row["id"] for row in report["open"]}
    covered = covered_ids(report)
    for predicate_id in sorted(open_ids - excused):
        defects.append({
            "code": "UNDECLARED_UNCOVERED",
            "detail": f"{predicate_id} is uncovered and uncovered_on_purpose does not name it",
        })
    for predicate_id in sorted(excused - open_ids):
        reason = "it is now covered" if predicate_id in covered else "SPEC.md does not state it"
        defects.append({
            "code": "STALE_EXCLUSION",
            "detail": f"uncovered_on_purpose names {predicate_id} and {reason}",
        })
    return defects


def stall(contract: dict) -> dict:
    """How far the floor has travelled, in commits, and whether it is over ceiling."""
    declared = contract["stall"]
    distance = commits_since(contract["floor"]["set_at_commit"])
    return {
        "commits_since_floor": distance,
        "ceiling": declared["ceiling_commits"],
        "over_ceiling": distance is not None and distance > declared["ceiling_commits"],
        "floor_commit_reachable": distance is not None,
        "refuses": bool(declared["refuses"]),
    }


def cmd_check(_: argparse.Namespace) -> int:
    """Grade the reading. Only a refusing defect changes the exit code."""
    contract = _contract()
    report = sov_f2_gate.read_gate()
    defects = grade(report, contract)
    drift = stall(contract)
    active = status_phase()
    active_defects: list[dict] = []
    if active and active != "NONE_ACTIVE" and active != contract.get("historical_phase"):
        from sovcustody import model as custody_model
        active_defects = grade_active_phase(
            active, phase_record(active),
            (contract.get("active_phase_profiles") or {}).get(active),
            custody_model.custodies(active),
        )
    defects.extend(active_defects)

    covered, total = report["predicates_covered"], report["predicates_total"]
    print(f"phase gate: {covered}/{total} predicates, floor {contract['floor']['total']}")
    for family, counts in report["by_family"].items():
        have = counts["total"] - counts["open"]
        declared = contract["floor"]["by_family"].get(family, 0)
        print(f"  {family:12} {have:3}/{counts['total']:<3} floor {declared}")

    pinned = contract["floor"]["set_at_commit"][:8]
    if not drift["floor_commit_reachable"]:
        print(f"  stall     floor commit {pinned} is not in this history; "
              f"the distance is unmeasurable here")
    elif drift["over_ceiling"]:
        print(f"  DEBT      {drift['commits_since_floor']} commits since the floor moved, "
              f"ceiling {drift['ceiling']}; recorded, not refused")
    else:
        print(f"  stall     {drift['commits_since_floor']} commits since the floor moved, "
              f"ceiling {drift['ceiling']}")

    if active == "NONE_ACTIVE":
        print("  active    NONE_ACTIVE; historical non-regression remains enforced")
    elif active and active != contract.get("historical_phase"):
        profile = (contract.get("active_phase_profiles") or {}).get(active)
        state = "initialized" if profile else "UNINITIALIZED"
        print(f"  active    {active} progress profile {state}")
    for defect in defects:
        print(f"  {defect['code']}: {defect['detail']}")
    if defects:
        print(f"FAIL: {len(defects)} phase-progress defect(s)")
        return 1
    print("PASS: the gate reading meets its floor and every gap below it is declared")
    return 0


def cmd_raise(args: argparse.Namespace) -> int:
    """Rewrite the floor to the current reading. Refuses to lower it."""
    contract = _contract()
    active = status_phase()
    if active not in ("", "NONE_ACTIVE", contract.get("historical_phase")):
        print(f"REFUSED: raise-floor is the historical {contract.get('historical_phase')} reader; "
              f"initialize {active} exit-custody floors in the phase opening/progress record")
        return 1
    report = sov_f2_gate.read_gate()
    covered = report["predicates_covered"]
    if covered < contract["floor"]["total"]:
        print(f"REFUSED: the reading is {covered} and the floor is "
              f"{contract['floor']['total']}; a floor is not lowered here")
        return 1
    contract["floor"]["total"] = covered
    contract["floor"]["by_family"] = {
        family: counts["total"] - counts["open"]
        for family, counts in report["by_family"].items()
    }
    contract["floor"]["set_at_commit"] = args.commit
    contract["floor"]["set_on"] = args.on
    (ROOT / CONTRACT).write_bytes((json.dumps(contract, indent=2) + "\n").encode("utf-8"))
    print(f"floor raised to {covered} at {args.commit[:8]}; "
          f"uncovered_on_purpose still needs the closed entries removed")
    return 0


def cmd_read(_: argparse.Namespace) -> int:
    """Print the reading, the floor, and the stall as JSON."""
    contract = _contract()
    active = status_phase()
    print(json.dumps({
        "historical_phase": contract.get("historical_phase"),
        "reading": sov_f2_gate.read_gate()["predicates_covered"],
        "floor": contract["floor"],
        "stall": stall(contract),
        "active_phase": active or None,
        "active_profile": (contract.get("active_phase_profiles") or {}).get(active),
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("check", help="grade the reading against the floor").set_defaults(run=cmd_check)
    sub.add_parser("read", help="print the reading, floor, and stall").set_defaults(run=cmd_read)
    raiser = sub.add_parser("raise-floor", help="set the floor to the current reading")
    raiser.add_argument("--commit", required=True, help="the commit the new floor is pinned to")
    raiser.add_argument("--on", required=True, metavar="YYYY-MM-DD",
                        help="the date the floor was set")
    raiser.set_defaults(run=cmd_raise)
    args = parser.parse_args(argv)
    if not getattr(args, "run", None):
        return cmd_check(args)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
