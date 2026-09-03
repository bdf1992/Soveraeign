#!/usr/bin/env python3
"""Strategy-neutral logical oracle for the Phase-I observation contract.

This module owns the run: reading the case file and any submitted observations,
refusing a report it cannot evaluate, and printing the suite verdict. The nine
requirement predicates it judges against live in `conformance/requirements.py`,
which also carries the kernel transition and discovery rows from
`conformance/kernel_predicates.py`.

Coverage is graded against two sets. A control run must carry both polarities for
every key in the table. A participant run must cover the nine PRD requirements and
whichever kernel rows its own case file declares: a participant that meets all nine
is not held to rows it never claimed, and one that claims a row is held to it.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from requirements import CHECKS, PRD_REQUIREMENTS, REQUIREMENTS


ROOT = Path(__file__).resolve().parent


class ObservationError(Exception):
    """The case file or participant report cannot be evaluated at all."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def observations_by_id(path: Path | None, cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index observations by case id, refusing any report that cannot be read as submitted.

    The submitter chooses what to send, so this refuses rather than resolves. A repeated
    case id used to be silently last-wins: an honest failing observation followed by a
    fabricated passing one under the same id produced SUITE PASS with no signal that a
    choice had been made. Refusing is the only reading that keeps the verdict the
    oracle's rather than the submitter's.
    """
    if path is None:
        origin = "case file"
        entries: Any = [{"case_id": case.get("id"), "observed": case.get("observed")}
                        for case in cases if isinstance(case, dict)]
    else:
        origin = "participant report"
        entries = load_json(path)
    if not isinstance(entries, list):
        raise ObservationError(f"{origin} must be a JSON array of observations")
    by_id: dict[str, dict[str, Any]] = {}
    for position, item in enumerate(entries):
        if not isinstance(item, dict):
            raise ObservationError(f"{origin} entry {position} is not an object")
        case_id = item.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise ObservationError(f"{origin} entry {position} has no case_id")
        if case_id in by_id:
            raise ObservationError(f"{origin} repeats an observation for {case_id}")
        observed = item.get("observed")
        if not isinstance(observed, dict):
            raise ObservationError(f"{origin} observation {case_id} has no observed object")
        by_id[case_id] = observed
    return by_id


def refuse(reason: str, as_json: bool) -> int:
    """Report a whole run as INVALID, the verdict conformance/README.md reserves for this."""
    report = {"suite": "INVALID", "results": [], "refused": reason,
              "missing_positive_and_defeating_coverage": []}
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"INVALID {reason}")
        print("SUITE   INVALID cases=0 coverage_gaps=0")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT / "oracle-controls.json")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    cases = load_json(args.cases)
    try:
        supplied = observations_by_id(args.observations, cases)
    except ObservationError as error:
        return refuse(str(error), args.as_json)
    results = []
    if args.observations is None:
        required_keys = set(REQUIREMENTS)
    else:
        declared = {case.get("requirement") for case in cases} & set(REQUIREMENTS)
        required_keys = set(PRD_REQUIREMENTS) | declared
    seen: dict[str, set[str]] = {requirement: set() for requirement in required_keys}
    suite_ok = True

    for case in cases:
        case_id = case.get("id")
        requirement = case.get("requirement")
        polarity = case.get("polarity")
        expected = case.get("expected_oracle") if args.observations is None else None
        valid_polarities = {"positive", "defeating"} if args.observations is None else {"participant"}
        if requirement not in CHECKS or polarity not in valid_polarities or case_id not in supplied:
            result = {"case_id": case_id, "requirement": requirement, "verdict": "INVALID", "defects": ["invalid or missing case observation"]}
            suite_ok = False
        else:
            seen.setdefault(requirement, set()).add(polarity)
            defects = CHECKS[requirement](supplied[case_id])
            verdict = "FAIL" if defects else "PASS"
            result = {"case_id": case_id, "requirement": requirement, "polarity": polarity, "verdict": verdict, "defects": defects}
            if expected is not None and verdict != expected:
                result["oracle_mismatch"] = {"expected": expected, "actual": verdict}
                suite_ok = False
            if args.observations is not None and verdict != "PASS":
                suite_ok = False
        results.append(result)

    required_polarities = {"positive", "defeating"} if args.observations is None else {"participant"}
    missing_coverage = sorted(requirement for requirement, polarities in seen.items()
                              if polarities != required_polarities)
    if missing_coverage:
        suite_ok = False

    report = {"suite": "PASS" if suite_ok else "FAIL", "results": results,
              "missing_positive_and_defeating_coverage": missing_coverage}
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"{result['verdict']:7} {result.get('case_id')} {result.get('requirement')} defects={len(result.get('defects', []))}")
        print(f"SUITE   {report['suite']} cases={len(results)} coverage_gaps={len(missing_coverage)}")
    return 0 if suite_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
