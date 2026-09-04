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

from sovcheckrun import dispatch, resolve  # noqa: E402
from sovcustody import model as custody_model  # noqa: E402

DEBT_CONTRACT = "contracts/closure-checks.json"

REFUSALS = {
    "CLOSURE_CHECK_UNPARSEABLE":
        "the expression is not a command line this reader can split",
    "CLOSURE_CHECK_COMPOUND":
        "the expression chains more than one command, so which stage closes the custody "
        "is undeclared",
    "CLOSURE_CHECK_NOT_PYTHON":
        "the expression names no python target this reader knows how to drive",
    "CLOSURE_CHECK_TARGET_MISSING":
        "the expression names a file or module that does not exist",
    "CLOSURE_CHECK_AMBIGUOUS":
        "the dotted module name matches more than one file, so the target is undeclared",
    "CLOSURE_CHECK_MUTE":
        "the target has no entry point, so running it exits 0 in silence",
    "CLOSURE_CHECK_REJECTED":
        "the target exists and refuses the declared arguments",
    "CLOSURE_CHECK_UNIMPORTABLE":
        "the target cannot be imported as declared",
    "CLOSURE_CHECK_UNSETTLEABLE":
        "the custody has neither a check nor a judgement seat, so nothing can close it",
}

DISPATCH_REFUSALS = {
    dispatch.REJECTED: "CLOSURE_CHECK_REJECTED",
    dispatch.UNIMPORTABLE: "CLOSURE_CHECK_UNIMPORTABLE",
}


def debt_contract(root: Path = ROOT) -> dict[str, Any]:
    return json.loads((root / DEBT_CONTRACT).read_bytes().decode("utf-8"))


def _defect(code: str, custody_id: str, detail: str) -> dict[str, str]:
    return {"code": code, "custody": custody_id, "detail": detail}


def grade_check(custody: dict[str, Any], root: Path = ROOT) -> list[dict[str, str]]:
    """Grade one custody's declared closure route."""
    custody_id = str(custody.get("custody_id") or "unnamed custody")
    closure = custody.get("closure") or {}
    check = closure.get("check")

    if not check:
        if not closure.get("judgement_seat"):
            return [_defect("CLOSURE_CHECK_UNSETTLEABLE", custody_id,
                            f"{custody_id} declares neither a check nor a judgement seat")]
        return []
    if str(check.get("kind")) != "COMMAND":
        return []

    expression = str(check.get("expression") or "")
    target = resolve.resolve(root, expression)
    if target.refusal:
        return [_defect(target.refusal, custody_id,
                        f"{custody_id} closure check {expression!r}: {REFUSALS[target.refusal]}")]

    if target.mode == "path" and not resolve.has_entry_point(target.path):
        relative = target.path.relative_to(root).as_posix()
        return [_defect("CLOSURE_CHECK_MUTE", custody_id,
                        f"{custody_id} closure check {expression!r} resolves to {relative}, "
                        f"which {REFUSALS['CLOSURE_CHECK_MUTE']}")]

    code, message = dispatch.probe(root, target.mode, target.target, target.argv)
    refusal = DISPATCH_REFUSALS.get(code)
    if refusal:
        return [_defect(refusal, custody_id,
                        f"{custody_id} closure check {expression!r}: {message or REFUSALS[refusal]}")]
    if code == dispatch.NO_PARSER and target.mode == "module":
        return [_defect("CLOSURE_CHECK_MUTE", custody_id,
                        f"{custody_id} closure check {expression!r} ran without reading an "
                        "argument, so the declared arguments were never accepted")]
    return []


def grade(records: list[dict[str, Any]] | None = None, root: Path = ROOT,
          entries: list[dict[str, Any]] | None = None,
          ) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Return (refusals, carried debt) over every custody in every collection.

    `entries` overrides the checked-in debt list. Only a test passes it: the two
    refusals that guard the list against going stale cannot both be driven from a
    contract that is, by construction, currently accurate.
    """
    rows = custody_model.custodies() if records is None else records
    debt_entries = debt_contract(root).get("debt", []) if entries is None else entries
    carried = {(entry["custody_id"], entry["expression"]): entry for entry in debt_entries}

    refusals: list[dict[str, str]] = []
    debt: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for custody in rows:
        custody_id = str(custody.get("custody_id") or "")
        check = (custody.get("closure") or {}).get("check") or {}
        expression = str(check.get("expression") or "")
        key = (custody_id, expression)
        found = grade_check(custody, root)
        if key in carried:
            seen.add(key)
            if not found:
                refusals.append(_defect(
                    "CLOSURE_CHECK_DEBT_REPAIRED", custody_id,
                    f"{custody_id} is recorded in {DEBT_CONTRACT} as not dispatching, and it "
                    "now dispatches; delete the entry rather than leaving it as cover"))
            else:
                debt.extend(found)
            continue
        refusals.extend(found)

    for custody_id, expression in sorted(set(carried) - seen):
        refusals.append(_defect(
            "CLOSURE_CHECK_DEBT_UNKNOWN", custody_id,
            f"{DEBT_CONTRACT} carries {custody_id} with {expression!r}, which no collection "
            "declares"))
    return refusals, debt


def _kind_census(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Every closure route by kind, so a kind this reader does not drive is visible."""
    census: dict[str, int] = {}
    for custody in rows:
        check = (custody.get("closure") or {}).get("check")
        kind = str(check.get("kind")) if check else "NONE (settled by a seat)"
        census[kind] = census.get(kind, 0) + 1
    return census


def cmd_check(args: argparse.Namespace) -> int:
    """Report the grade over the checked-in custody collections."""
    rows = custody_model.custodies()
    refusals, debt = grade(rows)
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

    declared = set(REFUSALS) | set(debt_contract().get("refuses", {}))
    exercised = {expected for expected, _ in _fixtures()}
    unexercised = sorted(declared - exercised - {"CLOSURE_CHECK_DEBT_REPAIRED",
                                                 "CLOSURE_CHECK_DEBT_UNKNOWN",
                                                 "CLOSURE_CHECK_DEBT_UNATTRIBUTED"})
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
