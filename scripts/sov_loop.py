#!/usr/bin/env python3
"""Tier loop command line.

Runs one Control -> Orchestration -> Work operation with an independent
observation, each tier on the model binding `contracts/tier-bindings.json`
declares for it, and audits the result against the separation rules `SDLC.md`
states in prose.

`run` reaches the operator's local Ollama runtime and consumes resources.
`selfcheck`, `audit`, and `table` touch no network.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sovloop import rules  # noqa: E402
from sovloop import run as loop  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "conformance" / "fixtures" / "loop" / "tier-cases.json"


def command_table(_: argparse.Namespace) -> int:
    """Print which model each tier runs on and what it may not do."""
    table = rules.load_table(ROOT)
    print(f"{table['table_id']} ({table['status']}) compiled from {table['compiles']}")
    print()
    for tier in table["tier_order"]:
        entry = table["tiers"][tier]
        print(f"  {tier:<14} {entry['binding_id']}")
        print(f"  {'':<14} may      {', '.join(entry['capabilities'])}")
        print(f"  {'':<14} may not  {', '.join(entry['may_not'])}")
        print(f"  {'':<14} ceiling  {entry['max_effect_class']}")
        print()
    observation = table["observation"]
    print(f"  {'OBSERVATION':<14} {observation['observer_binding_id']}")
    print(f"  {'':<14} must differ from {observation['must_differ_from']}")
    return 0


def command_audit(args: argparse.Namespace) -> int:
    """Audit one run record against the separation rules."""
    record = json.loads(Path(args.run).read_bytes().decode("utf-8"))
    defects = rules.audit(record, rules.load_table(ROOT))
    for defect in defects:
        print(f"REFUSED {defect}")
    if defects:
        print(f"\nFAIL: {len(defects)} separation defect(s)")
        return 1
    print("PASS: the run satisfies every declared separation rule")
    return 0


def command_selfcheck(_: argparse.Namespace) -> int:
    """Run the declared positive and defeating corpus without a network."""
    corpus = json.loads(FIXTURES.read_bytes().decode("utf-8"))
    table = rules.load_table(ROOT)
    failures: list[str] = []
    for case in corpus["cases"]:
        defects = rules.audit(case["run"], table)
        observed = sorted({defect.split(":", 1)[0] for defect in defects})
        expected = sorted(case["expect_refusals"])
        if observed != expected:
            failures.append(f"{case['case_id']}: expected {expected}, observed {observed}")
    for failure in failures:
        print(f"FAIL: {failure}")
    if failures:
        print(f"\nFAIL: {len(failures)} of {len(corpus['cases'])} tier loop cases")
        return 1
    positive = sum(1 for case in corpus["cases"] if not case["expect_refusals"])
    print(f"PASS: {len(corpus['cases'])} tier loop cases "
          f"({positive} positive, {len(corpus['cases']) - positive} defeating); "
          f"{len(rules.CHECKS)} separation rules exercised")
    return 0


def command_run(args: argparse.Namespace) -> int:
    """Run the loop live against the local Ollama runtime."""
    from sovloop import ollama

    table = rules.load_table(ROOT)
    try:
        record = loop.execute(args.objective, table, ollama.invoke, args.at)
    except ollama.Refusal as refusal:
        print(f"REFUSED {refusal}")
        return 1

    for tier in ("CONTROL", "ORCHESTRATION", "WORK", "OBSERVE"):
        text = record["transcript"].get(tier, "").strip()
        print(f"--- {tier} ---")
        print(text[:args.excerpt] + ("..." if len(text) > args.excerpt else ""))
        print()
    for defect in record["defects"]:
        print(f"REFUSED {defect}")
    print(f"settlement: {record['settlement']['outcome']}; "
          f"{len(record['invocations'])} invocations, {len(record['receipts'])} receipts")
    if args.out:
        Path(args.out).write_bytes(
            (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        print(f"run record written to {args.out}")
    return 1 if record["defects"] else 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every loop subcommand."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("table", help="print the tier binding table").set_defaults(
        handler=command_table)
    sub.add_parser("selfcheck", help="run the declared fixture corpus").set_defaults(
        handler=command_selfcheck)

    audit = sub.add_parser("audit", help="audit one run record")
    audit.add_argument("--run", required=True, help="path to a run record")
    audit.set_defaults(handler=command_audit)

    live = sub.add_parser("run", help="run the loop against the local runtime")
    live.add_argument("--objective", required=True, help="what the run is for")
    live.add_argument("--at", default="1970-01-01T00:00:00Z", help="declared run timestamp")
    live.add_argument("--out", help="write the full run record here")
    live.add_argument("--excerpt", type=int, default=600, help="characters shown per tier")
    live.set_defaults(handler=command_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one loop subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
