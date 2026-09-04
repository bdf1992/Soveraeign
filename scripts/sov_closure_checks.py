#!/usr/bin/env python3
"""Prove every declared custody closure check is a command that actually dispatches.

`contracts/custody.schema.json` calls the closure check "a closure condition
somebody can run", and it validates the shape of the expression: a `kind` and a
non-empty string. Nothing until now read the string. A custody could therefore
name a module with no entry point, or a subcommand a CLI stopped having, and
running the declared check would exit 2 into a usage message - or exit 0 in
silence, green because it is mute, which is trap T2 aimed at a phase gate rather
than at the verification suite.

    check       grade every custody closure check in every collection
    selfcheck   prove every declared refusal fires against a fixture

The reading drives each command as far as its argument parser and stops there.
That is stronger than resolving a path - it catches a renamed subcommand, a
removed flag, and a package that is not on the path - and weaker than running
the check, which is deliberate: several declared checks read live inventory and
one of them names an admission. `scripts/sovcheckrun/dispatch.py` owns that line.

Commands that already failed this reading when it was written are carried in
`contracts/closure-checks.json` as attributed debt rather than a refusal, on the
reasoning `scripts/sov_phase_progress.py` uses for the phase floor: a fall is
attributable to the edit that caused it and refuses, a stall is printed and
carried. An entry that starts dispatching fails here, so the list cannot outlive
the breakage it records.

Nothing here settles anything. A closure check that dispatches grants no standing
and does not mean the custody is closed - `check` reporting PASS says the gate can
speak, never that it said yes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovcheckrun.grade import (  # noqa: E402
    DEBT_CONTRACT, DEBT_SCHEMA, REFUSALS, _defect, _kind_census, debt_contract,
    debt_schema_defects, grade, grade_check,
)
from sovcustody import model as custody_model  # noqa: E402

def cmd_check(args: argparse.Namespace) -> int:
    """Report the grade over the checked-in custody collections."""
    rows = custody_model.custodies()
    refusals, debt = grade(rows)
    refusals = [_defect("CLOSURE_CHECK_DEBT_UNATTRIBUTED", DEBT_CONTRACT, problem)
                for problem in debt_schema_defects()] + refusals
    census = _kind_census(rows)
    if args.as_json:
        print(json.dumps({"custodies": len(rows), "kinds": census,
                          "defects": refusals, "debt": debt}, indent=2, sort_keys=True))
        return 1 if refusals else 0

    for kind, count in sorted(census.items()):
        graded = "driven to its parser" if kind == "COMMAND" else "counted, not driven"
        print(f"  {count:3d} {kind}: {graded}")
    for entry in debt:
        print(f"DEBT {entry['code']} {entry['detail']}")
    for defect in refusals:
        print(f"DEFECT {defect['code']} {defect['detail']}")
    if refusals:
        print(f"FAIL: {len(refusals)} closure check(s) nobody can run")
        return 1
    commands = census.get("COMMAND", 0)
    carried = f"; {len(debt)} carried as attributed debt in {DEBT_CONTRACT}" if debt else ""
    print(f"PASS: {commands - len(debt)} of {commands} command closure check(s) across "
          f"{len(rows)} custodies reach their argument parser{carried}")
    return 0


def _fixtures() -> list[tuple[str, dict[str, Any]]]:
    """One custody per declared refusal, each shaped to fire exactly that refusal."""
    def custody(name: str, expression: str | None, seat: str | None = "seat:root") -> dict:
        check = None if expression is None else {"kind": "COMMAND", "expression": expression}
        return {"custody_id": f"custody:fixture/{name}",
                "closure": {"check": check, "judgement_seat": seat, "defeated_by": "fixture"}}

    mute = "python scripts/sovcheckrun/fixtures/mute_docstring_guard.py"
    return [
        ("CLOSURE_CHECK_UNPARSEABLE", custody("unparseable", 'python "scripts/x.py')),
        ("CLOSURE_CHECK_COMPOUND",
         custody("compound", f"python scripts/sov_closure_checks.py check && {mute}")),
        ("CLOSURE_CHECK_NOT_PYTHON", custody("not-python", "make closure")),
        ("CLOSURE_CHECK_TARGET_MISSING", custody("missing", "python scripts/sov_no_such.py")),
        ("CLOSURE_CHECK_AMBIGUOUS", custody("ambiguous", "python -m cli")),
        ("CLOSURE_CHECK_MUTE", custody("mute", f"python {mute}")),
        ("CLOSURE_CHECK_REJECTED",
         custody("rejected", "python scripts/sov_closure_checks.py no-such-subcommand")),
        ("CLOSURE_CHECK_UNIMPORTABLE", custody("unimportable", "python -m sovcheckrun.dispatch")),
        ("CLOSURE_CHECK_UNSETTLEABLE", custody("unsettleable", None, seat=None)),
    ]


def _debt_fixtures() -> list[tuple[str, list[dict[str, Any]], list[dict[str, Any]]]]:
    """One (records, debt entries) pair per guard on the debt list itself."""
    working = "python scripts/sov_closure_checks.py check"
    broken = "python scripts/sov_node.py admit --session current"

    def custody(name: str, expression: str) -> dict[str, Any]:
        return {"custody_id": f"custody:fixture/{name}", "closure": {
            "check": {"kind": "COMMAND", "expression": expression},
            "judgement_seat": "seat:root", "defeated_by": "fixture"}}

    def entry(name: str, expression: str, **fields: str) -> dict[str, Any]:
        base = {"custody_id": f"custody:fixture/{name}", "expression": expression,
                "observed": "an observed error", "reason": "a stated reason",
                "repair_seat": "seat:root", "repair": "a stated repair"}
        base.update(fields)
        return base

    return [
        ("CLOSURE_CHECK_DEBT_REPAIRED",
         [custody("healed", working)], [entry("healed", working)]),
        ("CLOSURE_CHECK_DEBT_UNKNOWN",
         [], [entry("vanished", "python scripts/gone.py")]),
        ("CLOSURE_CHECK_DEBT_UNATTRIBUTED",
         [custody("bare", broken)], [entry("bare", broken, observed="", repair_seat="")]),
    ]


def cmd_selfcheck(_: argparse.Namespace) -> int:
    """Prove each declared refusal fires, and that a good custody fires none."""
    failures: list[str] = []
    for expected, fixture in _fixtures():
        codes = [defect["code"] for defect in grade_check(fixture)]
        if codes != [expected]:
            failures.append(f"{expected}: fixture produced {codes or 'no defect'}")
        else:
            print(f"REFUSES {expected}")

    admissible = {"custody_id": "custody:fixture/admissible", "closure": {
        "check": {"kind": "COMMAND", "expression": "python scripts/sov_closure_checks.py check"},
        "judgement_seat": "seat:root", "defeated_by": "fixture"}}
    if grade_check(admissible):
        failures.append("an admissible closure check was refused")
    else:
        print("ADMITS  a command that reaches its parser")

    for expected, records, entries in _debt_fixtures():
        codes = [defect["code"] for defect in grade(records, entries=entries)[0]]
        if codes != [expected]:
            failures.append(f"{expected}: fixture produced {codes or 'no defect'}")
        else:
            print(f"REFUSES {expected}")

    declared = set(REFUSALS) | set(debt_contract().get("refuses", {}))
    exercised = ({expected for expected, _ in _fixtures()}
                 | {expected for expected, _, _ in _debt_fixtures()})
    unexercised = sorted(declared - exercised)
    if unexercised:
        failures.append(f"declared refusals without a fixture: {unexercised}")

    for failure in failures:
        print(f"DEFECT {failure}")
    if failures:
        print(f"FAIL: {len(failures)} refusal(s) did not behave as declared")
        return 1
    print(f"PASS: {len(exercised)} declared refusal(s) fire and an admissible check passes")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", dest="as_json", action="store_true",
                        help="emit machine-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("check", help="grade every declared closure check")
    subparsers.add_parser("selfcheck", help="prove every declared refusal fires")
    args = parser.parse_args(argv)
    return cmd_check(args) if args.command == "check" else cmd_selfcheck(args)


if __name__ == "__main__":
    raise SystemExit(main())
