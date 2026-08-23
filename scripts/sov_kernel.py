#!/usr/bin/env python3
"""Kernel transition contract command line.

Reads `contracts/kernel-transitions.json`, the table compiled from the SPEC.md
Transition contract, and judges requests against it. It contacts no network,
touches no service, and records nothing: it answers whether a transition is
legal, never whether it happened.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import transitions as kernel  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "conformance" / "fixtures" / "kernel"


def _schema() -> dict[str, Any]:
    return json.loads((ROOT / "contracts" / "transition.schema.json").read_text("utf-8"))


def _corpus() -> dict[str, Any]:
    return json.loads((FIXTURES / "transition-cases.json").read_text(encoding="utf-8"))


def command_selfcheck(_: argparse.Namespace) -> int:
    """Run the declared positive and defeating kernel corpus without a network.

    Each case is judged twice: the request must satisfy the transition schema, and
    the evaluator's decision must match the case's declared expectation. A case
    that raises the wrong refusal fails as loudly as one that raises none, because
    a kernel that refuses for the wrong reason has not enforced the contract.
    """
    schema, corpus, table = _schema(), _corpus(), kernel.load_table(ROOT)
    failures: list[str] = []
    for case in corpus["cases"]:
        case_id, expect = case["case_id"], case["expect"]
        defects = validate(case["request"], schema)
        if defects:
            failures.append(f"{case_id}: request does not satisfy the schema: {defects[0]}")
            continue
        decision = kernel.evaluate(case["request"], table, case.get("current"))
        actual = "PERMITTED" if decision.permitted else decision.reason_code
        if actual != expect:
            failures.append(f"{case_id}: expected {expect}, observed {actual}")

    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\nFAIL: {len(failures)} of {len(corpus['cases'])} kernel transition cases")
        return 1

    declared = {entry["transition"] for entry in table["transitions"]}
    exercised = {case["request"]["transition"] for case in corpus["cases"]} & declared
    positive = sum(1 for case in corpus["cases"] if case["expect"] == "PERMITTED")
    print(
        f"PASS: {len(corpus['cases'])} kernel transition cases "
        f"({positive} positive, {len(corpus['cases']) - positive} defeating); "
        f"{len(exercised)} of {len(declared)} declared transitions exercised"
    )
    return 0


def command_check(args: argparse.Namespace) -> int:
    """Judge one transition request read from a file."""
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    current = json.loads(Path(args.current).read_text(encoding="utf-8")) if args.current else {}
    defects = validate(request, _schema())
    if defects:
        for defect in defects:
            print(f"FAIL: {defect}")
        return 1
    decision = kernel.evaluate(request, kernel.load_table(ROOT), current)
    print(decision.render())
    return 0 if decision.permitted else 1


def command_table(_: argparse.Namespace) -> int:
    """Print the declared transitions and what each one refuses."""
    table = kernel.load_table(ROOT)
    print(f"{table['table_id']} ({table['status']}) compiled from {table['compiles']}")
    print()
    for entry in table["transitions"]:
        marks = []
        if entry.get("requires_exact_pre_state"):
            marks.append("exact pre-state")
        if entry.get("requires_current_lease"):
            marks.append("current lease")
        if entry.get("requires_independent_observer"):
            marks.append("independent observer")
        if entry.get("requires_observation"):
            marks.append("observation")
        if entry.get("settles") is False:
            marks.append("never settles")
        print(f"  {entry['transition']:<18} -> {entry['commit']:<12} "
              f"refuses {', '.join(entry['refusals'])}")
        if marks:
            print(f"  {'':<18}    requires {'; '.join(marks)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every kernel subcommand."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    selfcheck = sub.add_parser("selfcheck", help="run the declared fixture corpus")
    selfcheck.set_defaults(handler=command_selfcheck)

    check = sub.add_parser("check", help="judge one transition request")
    check.add_argument("--request", required=True, help="path to a transition request")
    check.add_argument("--current", help="path to the observed current state")
    check.set_defaults(handler=command_check)

    table = sub.add_parser("table", help="print the declared transition table")
    table.set_defaults(handler=command_table)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one kernel subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
