#!/usr/bin/env python3
"""Prove every declared custody closure check is a command somebody can run.

`contracts/custody.schema.json` calls the closure check "a closure condition
somebody can run", and it validates the shape of the expression: a `kind` and a
non-empty string. Nothing until now read the string. A custody could therefore
name a module with no entry point, and running the declared check would exit 0
in silence - green because it is mute, which is trap T2 aimed at a phase gate
rather than at the verification suite.

    check       grade every custody closure check in every collection
    selfcheck   prove every declared refusal fires against a fixture

What this reads is resolution, not execution. It establishes that the named
target exists and exposes a runnable entry point; it does not run the command,
because several declared checks touch live inventory and one execution pass is
not something the verification suite should own. A check that resolves here can
still fail when run, which is the point of running it.

Nothing here settles anything. A resolvable closure check grants no standing and
does not mean the custody is closed.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import shlex
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovcustody import model as custody_model  # noqa: E402

ENTRY_POINT = '__name__ == "__main__"'

REFUSALS = {
    "CLOSURE_CHECK_UNRESOLVED":
        "the expression names no python target this reader can resolve",
    "CLOSURE_CHECK_TARGET_MISSING":
        "the expression names a file or module that does not exist",
    "CLOSURE_CHECK_MUTE":
        "the target has no runnable entry point, so running it exits 0 in silence",
    "CLOSURE_CHECK_UNSETTLEABLE":
        "the custody has neither a check nor a judgement seat, so nothing can close it",
}


def _module_path(dotted: str) -> Path | None:
    """Resolve a `python -m a.b.c` target wherever the repository lays that package out.

    Services keep their packages under `services/<domain>/src/`, the root keeps
    its own beside `scripts/`, and neither layout is declared anywhere this reader
    could consult. Matching the dotted path as a suffix finds both without this
    reader holding a list of source roots that a new service would silently fall off.
    """
    relative = Path(*dotted.split("."))
    for pattern in (f"**/{relative}.py", f"**/{relative}/__init__.py"):
        for candidate in sorted(ROOT.glob(pattern)):
            if ".git" in candidate.parts or "__pycache__" in candidate.parts:
                continue
            return candidate
    return None


def resolve(expression: str) -> tuple[Path | None, str | None]:
    """Return the file a closure expression would execute, or why it cannot be found."""
    try:
        tokens = shlex.split(expression)
    except ValueError:
        return None, "CLOSURE_CHECK_UNRESOLVED"
    if not tokens or Path(tokens[0]).name not in {"python", "python3"}:
        return None, "CLOSURE_CHECK_UNRESOLVED"

    rest = tokens[1:]
    if rest[:1] == ["-m"]:
        if len(rest) < 2:
            return None, "CLOSURE_CHECK_UNRESOLVED"
        found = _module_path(rest[1])
        return (found, None) if found else (None, "CLOSURE_CHECK_TARGET_MISSING")

    script = next((token for token in rest if token.endswith(".py")), None)
    if script is None:
        return None, "CLOSURE_CHECK_UNRESOLVED"
    target = ROOT / script
    return (target, None) if target.is_file() else (None, "CLOSURE_CHECK_TARGET_MISSING")


def grade_check(custody: dict[str, Any]) -> list[dict[str, str]]:
    """Grade one custody's declared closure route."""
    custody_id = str(custody.get("custody_id") or "unnamed custody")
    closure = custody.get("closure") or {}
    check = closure.get("check")

    if not check:
        if not closure.get("judgement_seat"):
            return [{"code": "CLOSURE_CHECK_UNSETTLEABLE", "custody": custody_id,
                     "detail": f"{custody_id} declares neither a check nor a judgement seat"}]
        return []

    if str(check.get("kind")) != "COMMAND":
        return []

    expression = str(check.get("expression") or "")
    target, code = resolve(expression)
    if code is not None:
        return [{"code": code, "custody": custody_id,
                 "detail": f"{custody_id} closure check {expression!r}: {REFUSALS[code]}"}]

    source = target.read_bytes().decode("utf-8")
    if ENTRY_POINT not in source:
        relative = target.relative_to(ROOT).as_posix()
        return [{"code": "CLOSURE_CHECK_MUTE", "custody": custody_id,
                 "detail": f"{custody_id} closure check {expression!r} resolves to {relative}, "
                           f"which {REFUSALS['CLOSURE_CHECK_MUTE']}"}]
    return []


def grade(records: list[dict[str, Any]] | None = None) -> list[dict[str, str]]:
    """Grade every custody in every collection."""
    rows = custody_model.custodies() if records is None else records
    return [defect for custody in rows for defect in grade_check(custody)]


def cmd_check(args: argparse.Namespace) -> int:
    """Report the grade over the checked-in custody collections."""
    rows = custody_model.custodies()
    defects = grade(rows)
    commands = sum(1 for row in rows
                   if (row.get("closure") or {}).get("check")
                   and str(((row.get("closure") or {}).get("check") or {}).get("kind")) == "COMMAND")
    if args.as_json:
        print(json.dumps({"custodies": len(rows), "commands": commands, "defects": defects},
                         indent=2, sort_keys=True))
        return 1 if defects else 0

    for defect in defects:
        print(f"DEFECT {defect['code']} {defect['detail']}")
    if defects:
        print(f"FAIL: {len(defects)} closure check(s) nobody can run")
        return 1
    print(f"PASS: {commands} command closure check(s) across {len(rows)} custodies resolve "
          "to a runnable entry point")
    return 0


def _fixtures() -> list[tuple[str, dict[str, Any]]]:
    """One custody per declared refusal, each shaped to fire exactly that refusal."""
    def custody(custody_id: str, closure: dict[str, Any]) -> dict[str, Any]:
        return {"custody_id": custody_id, "closure": closure}

    return [
        ("CLOSURE_CHECK_UNRESOLVED", custody("custody:fixture/unresolved", {
            "check": {"kind": "COMMAND", "expression": "make closure"},
            "judgement_seat": "seat:root", "defeated_by": "fixture"})),
        ("CLOSURE_CHECK_TARGET_MISSING", custody("custody:fixture/missing", {
            "check": {"kind": "COMMAND", "expression": "python scripts/sov_no_such_reader.py"},
            "judgement_seat": "seat:root", "defeated_by": "fixture"})),
        ("CLOSURE_CHECK_MUTE", custody("custody:fixture/mute", {
            "check": {"kind": "COMMAND", "expression": "python scripts/sovverify/shape.py"},
            "judgement_seat": "seat:root", "defeated_by": "fixture"})),
        ("CLOSURE_CHECK_UNSETTLEABLE", custody("custody:fixture/unsettleable", {
            "check": None, "judgement_seat": None, "defeated_by": "fixture"})),
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
        print("ADMITS  a resolvable command closure check")

    declared = set(REFUSALS)
    exercised = {expected for expected, _ in _fixtures()}
    if declared != exercised:
        failures.append(f"declared refusals without a fixture: {sorted(declared - exercised)}")

    for failure in failures:
        print(f"DEFECT {failure}")
    if failures:
        print(f"FAIL: {len(failures)} refusal(s) did not behave as declared")
        return 1
    print(f"PASS: {len(declared)} declared refusal(s) fire and an admissible check passes")
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
