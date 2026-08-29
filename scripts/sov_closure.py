#!/usr/bin/env python3
"""Judge a handoff: the moment a participant stops carrying a concern.

A bounded concern is accepted to be carried to a landed result. An issue, a
branch, a pull request, a review finding, a TODO, or a question to the owner
records work; none of them is work. This script grades a claimed handoff
against ``contracts/closure-ownership.json``, which admits five seams and
refuses everything else as reachable closure.

The table is data: the seams, the routine decisions, the absorption test, the
WIP ceiling, and the order refusals are reported in all live in the contract,
so changing what is admissible is a contract change with a fixture behind it
rather than an edit to this evaluator.

A refusal names what to do next as well as what was wrong. The contract's
``reachable_operations`` table declares, for every refusal code, the operations
that clear it, and no code may leave the refused participant with nothing it can
take alone. ``scripts/sovclosure/reachable.py`` owns reading and grading that
table.

``selfcheck`` grades the declared corpus in
``conformance/fixtures/closure/handoff-cases.json``; every refusal code in the
contract has at least one case proving it fires. It also grades the
reachable-operations table against
``conformance/fixtures/closure/reachable-operations-cases.json``. ``judge``
grades one claim file. ``next`` prints what clears one refusal code. ``loop``
prints the declared loop for a participant that wants to read it. Nothing here
contacts a network, writes standing, or grants anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sovclosure.reachable import corpus_defects, operations_for, table_defects  # noqa: E402
from sovclosure.rules import RULES  # noqa: E402

CONTRACT = ROOT / "contracts" / "closure-ownership.json"
CORPUS = ROOT / "conformance" / "fixtures" / "closure" / "handoff-cases.json"
REACHABLE_CORPUS = (ROOT / "conformance" / "fixtures" / "closure"
                    / "reachable-operations-cases.json")

PERMITTED = "PERMITTED"
REFUSED = "REFUSED"


def load_contract(path: Path = CONTRACT) -> dict:
    """Read the declared closure-ownership table."""
    return json.loads(path.read_text(encoding="utf-8"))


def judge(claim: dict, table: dict | None = None) -> dict:
    """Grade one handoff claim and return its verdict.

    Returns ``{"verdict": PERMITTED}`` or ``{"verdict": REFUSED, "refusal":
    <code>, "because": <reason>, "reachable_operations": [...]}``. The first
    refusal in the contract's declared evaluation order is the one reported,
    and it carries the operations that clear it, annotated against the tools
    the claim says this invocation granted.
    """
    table = table or load_contract()
    for code in table["evaluation_order"]:
        because = RULES[code](claim, table)
        if because:
            return {"verdict": REFUSED, "refusal": code, "because": because,
                    "means": table["refusals"][code],
                    "reachable_operations": operations_for(
                        table, code, claim.get("tools_available", []))}
    return {"verdict": PERMITTED, "seam": claim["seam"],
            "means": table["admissible_seams"][claim["seam"]]["means"]}


def selfcheck(corpus_path: Path = CORPUS) -> list[str]:
    """Grade the declared corpus and return one line per case that failed."""
    table = load_contract()
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    defects: list[str] = []
    for case in corpus["cases"]:
        verdict = judge(case["claim"], table)
        if verdict["verdict"] != case["expect"]:
            defects.append(
                f"{case['case_id']}: expected {case['expect']}, got {verdict['verdict']}"
                f" ({verdict.get('refusal', '-')})")
            continue
        if case["expect"] == REFUSED and verdict["refusal"] != case["refusal"]:
            defects.append(
                f"{case['case_id']}: expected refusal {case['refusal']},"
                f" got {verdict['refusal']}")
            continue
        if case["expect"] == REFUSED and not verdict["reachable_operations"]:
            defects.append(
                f"{case['case_id']}: refused with {verdict['refusal']} and no operation"
                " that clears it")
    covered = {c["refusal"] for c in corpus["cases"] if c["expect"] == REFUSED}
    for code in table["refusals"]:
        if code not in covered:
            defects.append(f"{code}: declared in the contract with no case proving it fires")
    defects.extend(table_defects(table))
    defects.extend(corpus_defects(
        table, json.loads(REACHABLE_CORPUS.read_text(encoding="utf-8"))))
    return defects


def _cmd_selfcheck(_args: argparse.Namespace) -> int:
    defects = selfcheck()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    reachable = json.loads(REACHABLE_CORPUS.read_text(encoding="utf-8"))
    for defect in defects:
        print(f"DEFECT {defect}")
    if defects:
        return 1
    print(f"closure ownership: {len(corpus['cases'])} declared cases judged as declared,"
          f" {len(reachable['table_cases'])} proving every refusal leaves an operation"
          f" reachable, {len(reachable['availability_cases'])} proving the annotation reads"
          " against the tools an invocation granted")
    return 0


def _cmd_judge(args: argparse.Namespace) -> int:
    claim = json.loads(Path(args.claim).read_text(encoding="utf-8"))
    verdict = judge(claim)
    if args.as_json:
        print(json.dumps(verdict, indent=2))
    elif verdict["verdict"] == PERMITTED:
        print(f"PERMITTED  {verdict['seam']}: {verdict['means']}")
    else:
        print(f"REFUSED  {verdict['refusal']}: {verdict['because']}")
        print(f"         {verdict['means']}")
        print()
        _print_operations(verdict["reachable_operations"])
    return 0 if verdict["verdict"] == PERMITTED else 1


def _print_operations(operations: list[dict]) -> None:
    """Print the operations that clear a refusal, marking what is reachable now."""
    print("Reachable next operations:")
    for operation in operations:
        if operation["available"]:
            mark = "  - "
        elif operation["needs_other_participant"]:
            mark = "  ~ "
        else:
            mark = "  x "
        tool = operation["tool"] or "-"
        print(f"{mark}{operation['operation']}  [{tool}]")
    print("  -  reachable now    ~  needs another participant    x  needs a tool this"
          " invocation did not grant")
    if not any(operation["available"] for operation in operations):
        print()
        print("Nothing here is reachable with the tools this invocation granted. That is a"
              " missing capability, not a ruling: ask for the tool at DEPENDENCY_SEAM, of a"
              " tier that can change how the session is launched.")


def _cmd_next(args: argparse.Namespace) -> int:
    table = load_contract()
    if args.refusal not in table["refusals"]:
        print(f"unknown refusal {args.refusal!r};"
              f" declared: {', '.join(sorted(table['refusals']))}")
        return 1
    granted = args.tools or table["tools"]
    operations = operations_for(table, args.refusal, granted)
    if args.as_json:
        print(json.dumps(operations, indent=2))
        return 0
    print(f"{args.refusal}: {table['refusals'][args.refusal]}")
    if not args.tools:
        print(f"tools assumed: every declared tool ({', '.join(table['tools'])});"
              " name --tool to read this against what your invocation actually granted")
    print()
    _print_operations(operations)
    return 0


def _cmd_loop(_args: argparse.Namespace) -> int:
    table = load_contract()
    for step in table["loop"]:
        mark = "required" if step["required"] else "conditional"
        print(f"{step['step']:<16} {mark:<12} needs {step['tool']:<14} {step['note']}")
    print()
    print(f"WIP ceiling: {table['wip_policy']['max_unlanded_concerns_per_participant']}"
          " unlanded concern per participant")
    print("Absorb a follow-on when all hold: " + ", ".join(table["absorption_test"]["predicates"]))
    print("Seams a handoff may name: " + ", ".join(sorted(table["admissible_seams"])))
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the closure-ownership CLI."""
    parser = argparse.ArgumentParser(prog="sov_closure", description=__doc__.splitlines()[0])
    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("selfcheck", help="grade the declared corpus")
    check.set_defaults(func=_cmd_selfcheck)

    grade = subparsers.add_parser("judge", help="grade one handoff claim file")
    grade.add_argument("claim", help="path to a soveraeign-closure-handoff/v1 claim")
    grade.add_argument("--json", action="store_true", dest="as_json",
                       help="emit the verdict as JSON")
    grade.set_defaults(func=_cmd_judge)

    ahead = subparsers.add_parser("next", help="print the operations that clear one refusal")
    ahead.add_argument("refusal", help="a refusal code declared in the contract")
    ahead.add_argument("--tool", action="append", default=[], dest="tools",
                       help="a tool this invocation granted; repeat for each")
    ahead.add_argument("--json", action="store_true", dest="as_json",
                       help="emit the operations as JSON")
    ahead.set_defaults(func=_cmd_next)

    show = subparsers.add_parser("loop", help="print the declared closure loop")
    show.set_defaults(func=_cmd_loop)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
