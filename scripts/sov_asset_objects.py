#!/usr/bin/env python3
"""Run the asset-object case corpus against the predicates that judge it.

`conformance/fixtures/asset/object-cases.json` states one world per case and
what that world proves. `conformance/asset_objects.py` owns the predicates. This
script only loads, evaluates, and reports; it decides nothing about the model.

A case declared `VIOLATED` that comes back satisfied is the failure worth having:
it means an invariant stopped being enforced and the defeating fixture no longer
defeats anything. A case declared `SATISFIED` that comes back violated means a
lawful world was refused. Both fail the run.

Every invariant `SPEC.md` states must carry at least one case of each polarity,
which the suite asserts rather than assumes: an invariant with no defeating case
is an invariant nothing can disprove.

Effect class: RECORD_LOCAL. This reads two files and writes nothing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFORMANCE = ROOT / "conformance"
CORPUS = CONFORMANCE / "fixtures" / "asset" / "object-cases.json"

if str(CONFORMANCE) not in sys.path:  # oracle bootstrap; conformance/run.py precedent
    sys.path.insert(0, str(CONFORMANCE))

from asset_objects import PREDICATES  # noqa: E402  (after the bootstrap above)

SATISFIED = "SATISFIED"
VIOLATED = "VIOLATED"


class CorpusError(Exception):
    """The corpus cannot be evaluated at all."""


def load_corpus(path: Path = CORPUS) -> dict[str, Any]:
    """Read the case corpus, refusing a shape the runner cannot judge."""
    try:
        corpus = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as absent:
        raise CorpusError(f"no corpus at {path}") from absent
    if not isinstance(corpus.get("cases"), list) or not corpus["cases"]:
        raise CorpusError("corpus declares no cases")
    return corpus


def judge(case: dict[str, Any]) -> tuple[str, list[str]]:
    """Evaluate one case and return its observed polarity and the defects seen."""
    predicate = PREDICATES.get(case.get("invariant"))
    if predicate is None:
        raise CorpusError(f"{case.get('case_id')} names unknown invariant "
                          f"{case.get('invariant')!r}")
    expected = case.get("expect")
    if expected not in (SATISFIED, VIOLATED):
        raise CorpusError(f"{case.get('case_id')} declares no expectation")
    defects = predicate(case.get("world") or {})
    return (VIOLATED if defects else SATISFIED), defects


def polarity_coverage(cases: list[dict[str, Any]]) -> list[str]:
    """Every invariant needs a positive and a defeating case, or it proves nothing."""
    seen: dict[str, set[str]] = {}
    for case in cases:
        seen.setdefault(case.get("invariant"), set()).add(case.get("expect"))
    gaps = []
    for invariant in sorted(PREDICATES):
        polarities = seen.get(invariant, set())
        for missing in sorted({SATISFIED, VIOLATED} - polarities):
            gaps.append(f"{invariant} has no {missing.lower()} case")
    return gaps


def run(verbose: bool = False) -> tuple[list[str], int]:
    """Evaluate every case. Returns the failures and the number of cases run."""
    corpus = load_corpus()
    cases = corpus["cases"]
    failures = []
    for case in cases:
        observed, defects = judge(case)
        expected = case["expect"]
        if observed != expected:
            detail = defects[0] if defects else "no defect seen"
            failures.append(f"{case['case_id']}: declared {expected}, observed {observed} "
                            f"({detail})")
        elif verbose:
            print(f"  {observed:<9} {case['case_id']}")
    failures.extend(polarity_coverage(cases))
    return failures, len(cases)


def cmd_selfcheck(args: argparse.Namespace) -> int:
    """Prove every declared case behaves as the corpus says it does."""
    try:
        failures, total = run(verbose=args.verbose)
    except CorpusError as refused:
        print(f"REFUSED: {refused}")
        return 2
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        print(f"FAIL: {len(failures)} of {total} asset-object case(s) do not behave as declared")
        return 1
    positive = sum(1 for case in load_corpus()["cases"] if case["expect"] == SATISFIED)
    print(f"PASS: {total} asset-object cases across {len(PREDICATES)} invariants "
          f"({positive} positive, {total - positive} defeating); every defeating case defeats")
    print("Standing note: these grade the logical model in SPEC.md, not a participant. "
          "No implementation carries these objects yet.")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """Print every invariant and how many cases stand behind it."""
    corpus = load_corpus()
    counts: dict[str, list[str]] = {}
    for case in corpus["cases"]:
        counts.setdefault(case["invariant"], []).append(case["expect"])
    width = max(len(name) for name in PREDICATES)
    for invariant in sorted(PREDICATES):
        polarities = counts.get(invariant, [])
        positive = polarities.count(SATISFIED)
        defeating = polarities.count(VIOLATED)
        print(f"{invariant.ljust(width)}  {positive} positive  {defeating} defeating")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Command surface for the corpus."""
    parser = argparse.ArgumentParser(prog="sov_asset_objects",
                                     description="Asset object cases and the predicates "
                                                 "that judge them.")
    sub = parser.add_subparsers(dest="command", required=True)
    selfcheck = sub.add_parser("selfcheck", help="run the declared case corpus")
    selfcheck.add_argument("--verbose", action="store_true")
    selfcheck.set_defaults(handler=cmd_selfcheck)
    listing = sub.add_parser("list", help="every invariant and its case count")
    listing.set_defaults(handler=cmd_list)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
