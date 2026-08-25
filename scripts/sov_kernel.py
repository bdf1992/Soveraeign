#!/usr/bin/env python3
"""Shared Kernel projections and conformance command line.

The Shared Kernel is broader than any executable table: SPEC.md supplies its logical
typology, topology, traversal, and invariants. This command exposes machine-readable
projections of that grammar without turning the Kernel into a runtime service.

The transition commands read ``contracts/kernel-transitions.json``, the authored
executable projection of the SPEC.md Transition contract. The binding commands read
every service manifest plus ``contracts/kernel-paradigms.json`` and derive how those
participants compose against the same Kernel grammar.

Nothing here grants authority, touches a service, or settles an operation. These are
read/check/compiler surfaces: they answer what is declared and whether declarations
compose, never whether an effect happened.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovkernel import kernel_binding as binding_check  # noqa: E402
from sovkernel.closure_inputs import rebuild as rebuild_closure  # noqa: E402
from sovkernel import projection  # noqa: E402
from sovkernel import parity as parity_check  # noqa: E402
from sovkernel import transitions as kernel  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "conformance" / "fixtures" / "kernel"


def _schema() -> dict[str, Any]:
    return json.loads((ROOT / "contracts" / "transition.schema.json").read_text("utf-8"))


def _corpus() -> dict[str, Any]:
    return json.loads((FIXTURES / "transition-cases.json").read_text(encoding="utf-8"))


def _binding_inputs() -> tuple[
    dict[str, dict[str, Any]], dict[str, Any], dict[str, Any],
    list[dict[str, str]], list[str]
]:
    closure, manifests, transitions, paradigms, source_digests, defects = rebuild_closure(ROOT)
    del closure
    return manifests, transitions, paradigms, source_digests, defects


def command_selfcheck(_: argparse.Namespace) -> int:
    """Run the declared positive and defeating transition corpus without a network."""
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


def command_parity(_: argparse.Namespace) -> int:
    """Prove each participant already decides the way the transition projection decides."""
    failures, checked = parity_check.run(ROOT)
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"FAIL: {len(failures)} parity defect(s) across {checked} correspondences")
        return 1
    print(
        f"PASS: {checked} kernel parity correspondences; "
        "every participant refusal matches the kernel refusal it declares"
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


def command_drift(_: argparse.Namespace) -> int:
    """Refuse when the transition projection and SPEC.md disagree about traversal."""
    spec = (ROOT / "SPEC.md").read_bytes().decode("utf-8")
    derived = projection.derive(spec)
    defects = projection.invariants(derived) + projection.conflicts(
        derived, kernel.load_table(ROOT))
    for defect in defects:
        print(f"DRIFT   {defect}")
    if defects:
        print(f"FAIL: {len(defects)} disagreements between SPEC.md and "
              "contracts/kernel-transitions.json")
        return 1
    codes = sorted({code for row in derived.values() for code in row["refusals"]})
    print(f"PASS: {len(derived)} transitions and {len(codes)} named refusal codes stated "
          "by SPEC.md agree with the authored kernel table")
    return 0


def command_binding_check(_: argparse.Namespace) -> int:
    """Check that all authored service manifests compose as Kernel participants."""
    manifests, transitions, paradigms, _, source_defects = _binding_inputs()
    defects = source_defects + binding_check.binding_defects(manifests, transitions, paradigms)
    for defect in defects:
        print(f"BINDING {defect}")
    if defects:
        print(f"FAIL: {len(defects)} service-to-Kernel binding defect(s)")
        return 1

    operations = sum(len(manifest.get("operations", [])) for manifest in manifests.values())
    mapped = sum(1 for manifest in manifests.values()
                 for operation in manifest.get("operations", [])
                 if operation.get("kernel_transition"))
    print(
        f"PASS: {len(manifests)} service manifests compose as Kernel participants; "
        f"{len(paradigms.get('paradigms', []))} indexed paradigms; "
        f"{operations} operations, {mapped} mapped to named Kernel transitions, "
        f"{operations - mapped} explicitly unmapped"
    )
    return 0


def command_closure(_: argparse.Namespace) -> int:
    """Print the rebuildable service-to-Kernel closure as JSON for humans or agents."""
    manifests, transitions, paradigms, source_digests, source_defects = _binding_inputs()
    closure = binding_check.build(
        manifests, transitions, paradigms, source_digests=source_digests
    )
    closure_schema = json.loads(
        (ROOT / "contracts" / "kernel-closure.schema.json").read_text("utf-8")
    )
    paradigm_schema = json.loads(
        (ROOT / "contracts" / "kernel-paradigms.schema.json").read_text("utf-8")
    )
    defects = (
        source_defects
        + validate(paradigms, paradigm_schema)
        + validate(closure, closure_schema)
        + binding_check.binding_defects(manifests, transitions, paradigms)
    )
    print(json.dumps(closure, indent=2, sort_keys=True))
    if defects:
        for defect in defects:
            print(f"BINDING {defect}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every Kernel projection subcommand."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    selfcheck = sub.add_parser("selfcheck", help="run the declared transition fixture corpus")
    selfcheck.set_defaults(handler=command_selfcheck)

    parity = sub.add_parser("parity", help="check participants against transition semantics")
    parity.set_defaults(handler=command_parity)

    check = sub.add_parser("check", help="judge one transition request")
    check.add_argument("--request", required=True, help="path to a transition request")
    check.add_argument("--current", help="path to the observed current state")
    check.set_defaults(handler=command_check)

    drift = sub.add_parser("drift", help="compare the traversal projection against SPEC.md")
    drift.set_defaults(handler=command_drift)

    table = sub.add_parser("table", help="print the declared transition table")
    table.set_defaults(handler=command_table)

    binding = sub.add_parser(
        "binding-check",
        help="check all service manifests as equal participants in the Kernel grammar",
    )
    binding.set_defaults(handler=command_binding_check)

    closure = sub.add_parser(
        "closure",
        help="print the derived Node-wide service-to-Kernel closure as JSON",
    )
    closure.set_defaults(handler=command_closure)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one Kernel projection command."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
