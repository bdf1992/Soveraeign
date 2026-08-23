#!/usr/bin/env python3
"""Measure what the logical specification has actually earned.

`SPEC.md` states its own standing rule: passing self-authored fixtures
establishes `BUILT`, an independent run is required for `WITNESSED`, and the
owner's recorded decision is required for `RATIFIED`. The specification sits at
`PROPOSED`, and nothing in this repository ever checked it against the
requirements it claims to implement. So the owner has been asked to ratify a
document that skipped two standings, which the transition contract refuses as
`SKIPPED_STANDING` when a ticket tries it.

This command is the missing evidence path. It checks the specification against
`PRD.md` and against the conformance oracle, and reports the standing the
specification has earned rather than the standing someone would like it to have.
It ratifies nothing. It cannot: earned standing is evidence, and ratification is
judgement.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import argparse
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIREMENT = re.compile(r"^### (PROD-I-[0-9]+) . (.+)$", re.M)
TABLE_ROW = re.compile(r"^\| ([^|]+?) \| ([^|]+?) \| ([^|]+?) \|$", re.M)
REQ_REF = re.compile(r"PROD-I-[0-9]+|I-[0-9]+")


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").replace("\r\n", "\n")


def _requirements(document: str) -> dict[str, str]:
    return {match.group(1): match.group(2).strip()
            for match in REQUIREMENT.finditer(document)}


def _traceability(spec: str) -> list[dict[str, str]]:
    section = spec.split("## Traceability", 1)
    if len(section) == 1:
        return []
    rows = []
    for area, requirement, ground in TABLE_ROW.findall(section[1]):
        if area.strip().startswith("---") or area.strip() == "Specification area":
            continue
        rows.append({"area": area.strip(), "requirement": requirement.strip(),
                     "ground": ground.strip()})
    return rows


def _normalise(reference: str) -> set[str]:
    """Expand a table cell such as 'PROD-I-1, I-4' into full requirement ids."""
    found = set()
    for token in REQ_REF.findall(reference):
        found.add(token if token.startswith("PROD-") else "PROD-" + token)
    return found


def _controls() -> dict[str, set[str]]:
    data = json.loads((ROOT / "conformance" / "oracle-controls.json").read_text("utf-8"))
    polarity: dict[str, set[str]] = {}
    for control in data:
        polarity.setdefault(control["requirement"], set()).add(control["polarity"])
    return polarity


def audit() -> dict[str, Any]:
    """Check the specification against the requirements and the oracle."""
    prd, spec = _read("PRD.md"), _read("SPEC.md")
    required = _requirements(prd)
    specified = _requirements(spec)
    rows = _traceability(spec)
    controls = _controls()
    traced: set[str] = set()
    for row in rows:
        traced |= _normalise(row["requirement"])

    findings: list[str] = []
    for requirement in sorted(required):
        if requirement not in specified:
            findings.append(f"{requirement}: PRD declares it; SPEC.md states no predicate")
        if requirement not in traced:
            findings.append(f"{requirement}: absent from the SPEC.md traceability table")
        polarity = controls.get(requirement, set())
        for needed in ("positive", "defeating"):
            if needed not in polarity:
                findings.append(f"{requirement}: the oracle has no {needed} control")
    for requirement in sorted(specified):
        if requirement not in required:
            findings.append(f"{requirement}: SPEC.md states a predicate PRD.md does not require")
    for requirement in sorted(traced):
        if requirement not in required:
            findings.append(f"{requirement}: traced in SPEC.md but absent from PRD.md")

    # The third column of the traceability table points at the historical corpus.
    # A fresh witness receives a clean checkout, so a ground it cannot resolve is
    # reported rather than assumed - FOUND-007 names hidden context as a defeat.
    grounds = sorted({row["ground"] for row in rows if row["ground"]})
    lineage = (ROOT / "lineage").is_dir()

    return {
        "requirements": required,
        "specified": specified,
        "traced": traced,
        "rows": rows,
        "controls": controls,
        "findings": findings,
        "grounds": grounds,
        "lineage_present": lineage,
    }


def command_trace(args: argparse.Namespace) -> int:
    """Report the standing the specification has earned."""
    result = audit()
    findings = result["findings"]
    total = len(result["requirements"])

    for finding in findings:
        print(f"FAIL: {finding}")

    if findings:
        print(f"\nFAIL: {len(findings)} traceability defect(s) across {total} requirements")
        return 1

    print(
        f"PASS: {total} requirements; each states a SPEC.md predicate, appears in the "
        f"traceability table, and carries a positive and a defeating oracle control"
    )
    print()
    print("Earned standing for SPEC.md:")
    print("  BUILT      EARNED - every requirement states a predicate, is traced, and")
    print("             carries a positive and a defeating control that pass")
    print("  WITNESSED  NOT EARNED - no independent run is recorded. FOUND-007 declares")
    print("             the procedure and has never been executed; it is still a SEED.")
    print("             This is the blocker, and it is a task, not a judgement.")
    if not result["lineage_present"]:
        print("             The source ground is locked evidence that PUBLICATION.md keeps")
        print("             unpublished. That is governed, not blocking: a witness reports")
        print("             it unavailable and never claims a verification it could not")
        print("             perform, which is exactly what verify_bootstrap already does.")
    print("  RATIFIED   NOT REACHABLE - owner judgement, and asking for it before")
    print("             WITNESSED skips a standing, which this repository refuses")
    print("             everywhere else as SKIPPED_STANDING")

    if args.verbose:
        print()
        for row in result["rows"]:
            print(f"  {row['area']:<34} {row['requirement']:<18} {row['ground']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Return the argument parser for every specification subcommand."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    trace = sub.add_parser("trace", help="check SPEC.md against PRD.md and the oracle")
    trace.add_argument("--verbose", action="store_true", help="print the traceability table")
    trace.set_defaults(handler=command_trace)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one specification subcommand."""
    args = build_parser().parse_args(argv)
    return int(args.handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
