"""The subcommand bodies behind `scripts/sov_custody.py`.

Split from the entry point so the entry point stays an argparse shell and this
file stays the place a reader looks for what a command actually prints. Nothing
here settles anything; every command is a reading.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import board as boardmod  # noqa: E402
from sovcustody import circuit as circuitmod  # noqa: E402
from sovcustody import estimate as estimatemod  # noqa: E402
from sovcustody import model as modelmod  # noqa: E402
from sovcustody import phase as phasemod  # noqa: E402
from sovcustody import roots as rootsmod  # noqa: E402

FIXTURES = ROOT / "conformance" / "fixtures" / "custody" / "circuit-cases.json"


def command_list(args: argparse.Namespace) -> int:
    records = modelmod.custodies()
    if args.as_json:
        print(json.dumps(records, indent=2))
        return 0
    print(boardmod.summary(records))
    defects = modelmod.grade_collection(records)
    print()
    if defects:
        print(f"{len(defects)} defect(s)")
        for code, detail in defects:
            print(f"  {code:<28} {detail}")
        return 1
    print("collection admissible")
    return 0


def command_board(args: argparse.Namespace) -> int:
    custody = modelmod.by_id(args.custody_id)
    if custody is None:
        print(f"REFUSED: no custody named {args.custody_id}")
        return 1
    built = boardmod.build(custody, with_derived=not args.no_derived)
    if args.as_json:
        print(json.dumps(built, indent=2))
        return 0
    print(boardmod.render(built))
    return 0


def command_circuit(args: argparse.Namespace) -> int:
    stages = circuitmod.stages()
    if args.as_json:
        print(json.dumps(stages, indent=2))
        return 0
    for stage in stages:
        print(f"{stage['ordinal']}. {stage['stage']}")
        print(f"   {stage['means']}")
        for predicate in stage["admits_when"]:
            print(f"     admits when  {predicate}")
        defeat = stage["defeated_by"]
        print(f"     defeated by  {defeat['case']}: {defeat['means']}")
        print(f"                  {defeat['why']}")
        print()
    print("refusals")
    for code, means in sorted(circuitmod.declared_refusals().items()):
        print(f"  {code:<28} {means}")
    return 0


def command_estimate(args: argparse.Namespace) -> int:
    registry_defects = estimatemod.grade_registry()
    if registry_defects:
        for code, detail in registry_defects:
            print(f"  {code:<28} {detail}")
        return 1

    records = modelmod.custodies()
    if args.custody_id:
        records = [record for record in records if record["custody_id"] == args.custody_id]
        if not records:
            print(f"REFUSED: no custody named {args.custody_id}")
            return 1

    rows: list[dict] = []
    for custody in records:
        for row in estimatemod.variance(custody.get("estimate")):
            rows.append({**row, "custody_id": custody["custody_id"]})
    if args.as_json:
        print(json.dumps(rows, indent=2))
        return 0

    declared = estimatemod.dimensions()
    print(f"{len(declared)} declared dimensions"
          f" ({sum(1 for row in declared.values() if row.get('graded'))} graded)")
    for name, row in declared.items():
        source = row.get("actual_source") or f"ungraded - {row.get('ungraded_because', '')}"
        print(f"  {name:<22} {row['kind']:<13} {row['unit']:<12} {source}")
    print()
    print(f"{len(rows)} estimated dimension(s) across {len(records)} custody(ies)")
    for row in rows:
        actual = "-" if row["actual"] is None else row["actual"]
        print(f"  {row['custody_id']:<32} {row['dimension_id']:<22} "
              f"{row['low']:>8} .. {row['high']:<10} actual {actual:<8} {row['verdict']}")
    return 0


def command_reconcile(args: argparse.Namespace) -> int:
    """Every phase exit clause against the custody that holds it.

    The clauses are read from contracts/phases.json, which pins the defining
    documents by digest. Restating them here would be a second copy of the exit,
    and a second copy is where a narrowed definition enters.
    """
    records = {custody["custody_id"]: custody for custody in modelmod.custodies()}
    defects = phasemod.grade_collection(custody_ids=set(records))
    rows = []
    for phase in phasemod.phases():
        derived = phasemod.terminal_for(phase["execution_status"], phase["acceptance_status"])
        print(f"{phase['phase_id']}  {phase['title']}")
        print(f"  opened {phase['opened']}  closed {phase.get('closed') or '-'}")
        print(f"  execution {phase['execution_status']}   "
              f"acceptance {phase['acceptance_status']}   terminal {derived}")
        print(f"  settled by {phase.get('settled_by') or 'nobody'}")
        print()
        for pinned in phase.get("definition") or []:
            print(f"  pinned  {pinned['document']:<12} {pinned['digest']}")
        print()
        for clause in phase["exit_clauses"]:
            held = clause.get("held_by")
            print(f"  {clause['verdict']:<22} {clause['clause_id']}")
            print(f"     {clause['text']}")
            if clause.get("reading"):
                print(f"     {clause['reading']}")
            if held:
                custody = records.get(held)
                if custody is None:
                    print(f"     ORPHAN: {held} is not a declared custody")
                else:
                    built = boardmod.build(custody, with_derived=False)
                    children = [c["custody_id"] for c in records.values()
                                if c.get("serves_exit") == held]
                    print(f"     held by {held}, standing at "
                          f"{built['lowest_member_stage'] or built['entry_stage']}, "
                          f"targeting {built['target_stage']}")
                    if children:
                        print(f"     delivery: {', '.join(children)}")
            rows.append(clause["verdict"])
            print()

    outside = [c["custody_id"] for c in records.values() if c.get("outside_phase_exit")]
    if outside:
        print(f"{len(outside)} custody(ies) explicitly outside the phase exit:")
        for custody_id in outside:
            print(f"  {custody_id}  -  {records[custody_id]['outside_phase_exit']}")
        print()

    if defects:
        print(f"{len(defects)} defect(s)")
        for code, detail in defects:
            print(f"  {code:<28} {detail}")
        return 1
    earned = sum(1 for verdict in rows if verdict == "EARNED")
    print(f"{earned}/{len(rows)} clause(s) earned")
    return 0


def command_phase(args: argparse.Namespace) -> int:
    records = phasemod.phases()
    if args.as_json:
        print(json.dumps(records, indent=2))
        return 0
    custody_ids = {custody["custody_id"] for custody in modelmod.custodies()}
    defects = phasemod.grade_collection(records, custody_ids)
    for phase in records:
        derived = phasemod.terminal_for(phase["execution_status"], phase["acceptance_status"])
        print(f"{phase['phase_id']:<12} {phase['execution_status']:<8} "
              f"{phase['acceptance_status']:<12} {derived}")
    print()
    if defects:
        print(f"{len(defects)} defect(s)")
        for code, detail in defects:
            print(f"  {code:<28} {detail}")
        return 1
    print("phase records admissible")
    return 0


def _orphan_items() -> tuple[list[str], int, dict[str, int]]:
    """Derived work items that fall inside no custody, with a tally by owning service.

    Most of this repository's declared operations are not on the Phase-I exit
    path. That is admissible and it is worth knowing, which is why the count is
    a command rather than a number somebody wrote down once.
    """
    records = modelmod.custodies()
    items = boardmod.derived_items()
    held = {
        item["item_id"]
        for custody in records
        for item in boardmod.attached(custody, items)
    }
    orphaned = [item for item in items if item["item_id"] not in held]
    tally: dict[str, int] = {}
    for item in orphaned:
        service = str((item.get("subject") or {}).get("service_id") or "-")
        tally[service] = tally.get(service, 0) + 1
    addresses = [str((item.get("subject") or {}).get("address")) for item in orphaned]
    return addresses, len(items), tally


def command_orphans(args: argparse.Namespace) -> int:
    if args.kind == "ITEM":
        addresses, total, tally = _orphan_items()
        if args.as_json:
            print(json.dumps({"orphans": addresses, "derived_total": total, "by_service": tally},
                             indent=2))
            return 0
        print(f"{len(addresses)} of {total} derived work item(s) fall inside no custody")
        for service, count in sorted(tally.items(), key=lambda row: -row[1]):
            print(f"  {service:<14} {count:>4}")
        return 1 if addresses else 0

    missing = rootsmod.orphans(modelmod.custodies(), args.kind)
    if args.as_json:
        print(json.dumps(missing, indent=2))
        return 0
    print(f"{len(missing)} declared item(s) no custody holds"
          + (f" · kind={args.kind}" if args.kind else ""))
    for address in missing:
        print(f"  {address}")
    return 1 if missing else 0


def command_selfcheck(args: argparse.Namespace) -> int:
    """Prove every declared refusal fires against a fixture that defeats it."""
    cases = json.loads(FIXTURES.read_bytes().decode("utf-8"))
    expected = set(circuitmod.declared_refusals()) | set(estimatemod.declared_refusals()) \
        | set(modelmod.REFUSALS)
    fired: set[str] = set()
    failures: list[str] = []

    for case in cases:
        kind = case["judge"]
        if kind == "circuit":
            defects = circuitmod.judge_advance(
                case.get("from_stage", ""), case["to_stage"], case.get("evidence") or {},
                set(case.get("required_dimensions") or []))
        elif kind == "estimate":
            defects = estimatemod.grade(case.get("estimate"),
                                        set(case.get("required") or []), case.get("stage"))
        elif kind == "collection":
            defects = modelmod.grade_collection(case["custodies"])
        elif kind == "registry":
            defects = estimatemod.grade_registry(case["registry"])
        elif kind == "phase":
            defects = phasemod.grade(case["phase"], set(case.get("custody_ids") or []))
        else:
            defects = modelmod.grade(case["custody"], set(case.get("seats") or []))
        codes = {code for code, _ in defects}
        fired |= codes
        want = set(case.get("expect_refusals") or [])
        if case["polarity"] == "positive" and codes:
            failures.append(f"{case['id']}: admissible case refused by {sorted(codes)}")
        if case["polarity"] == "defeating" and not want <= codes:
            failures.append(f"{case['id']}: expected {sorted(want - codes)}, got {sorted(codes)}")

    # `fired` can carry codes outside the declared set - SCHEMA, raised by the
    # collection judge - so the reached count is intersected rather than taken raw.
    unreachable = sorted(expected - fired)
    reached = fired & expected
    print(f"{len(cases)} case(s), {len(reached)}/{len(expected)} declared refusals reached")
    for failure in failures:
        print(f"  FAIL  {failure}")
    for code in unreachable:
        print(f"  UNREACHED  {code}")
    if failures or unreachable:
        return 1
    print("selfcheck PASS")
    return 0
