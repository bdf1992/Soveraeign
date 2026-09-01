#!/usr/bin/env python3
"""Read and grade the repository candidate lifecycle contract.

This evaluator is deliberately effect-free. It answers whether a proposed carrier
transition preserves the repository's distinction between mutable construction,
frozen evidence subjects, and landing settlement. Git mechanics consume this
contract; this script does not move a ref, stage a file, or create authority.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "contracts" / "repository-candidate-lifecycle.json"
CASES_PATH = ROOT / "conformance" / "fixtures" / "repository-candidate" / "lifecycle-cases.json"

PERMITTED = "PERMITTED"
INVALID_OPERATION = "INVALID_OPERATION"
INVALID_STATE = "INVALID_STATE"
MISSING_PRECONDITION = "MISSING_PRECONDITION"
EVIDENCE_SUBJECT_MISMATCH = "EVIDENCE_SUBJECT_MISMATCH"
STALE_BASE = "STALE_BASE"


def load_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _missing(claim: dict, required: list[str]) -> list[str]:
    return [field for field in required if not claim.get(field)]


def _subject_mismatch(contract: dict, claim: dict) -> str | None:
    fields = contract["evidence_subject"]
    pairs = (
        (fields["address_field"], "evidence_candidate_commit"),
        (fields["content_field"], "evidence_candidate_tree"),
        (fields["base_field"], "evidence_base_commit"),
    )
    missing = [evidence for _subject, evidence in pairs if not claim.get(evidence)]
    if missing:
        return f"evidence is missing subject fields: {', '.join(missing)}"
    for subject, evidence in pairs:
        if claim.get(subject) != claim.get(evidence):
            return f"{evidence} does not match {subject}"
    return None


def evaluate(contract: dict, claim: dict) -> dict:
    operation = claim.get("operation")
    rule = contract.get("operations", {}).get(operation)
    if rule is None:
        return {"verdict": "REFUSED", "code": INVALID_OPERATION,
                "detail": f"unknown repository candidate operation {operation!r}"}

    state = claim.get("state")
    if state not in rule.get("from", []):
        return {"verdict": "REFUSED", "code": INVALID_STATE,
                "detail": f"{operation} is not admitted from {state!r}"}

    required = list(rule.get("requires", []))
    if rule.get("requires_new_candidate"):
        required.append("new_candidate_commit")
    missing = _missing(claim, required)
    if missing:
        return {"verdict": "REFUSED", "code": MISSING_PRECONDITION,
                "detail": f"{operation} requires: {', '.join(missing)}"}

    if rule.get("requires_exact_subject_match"):
        mismatch = _subject_mismatch(contract, claim)
        if mismatch:
            return {"verdict": "REFUSED", "code": EVIDENCE_SUBJECT_MISMATCH,
                    "detail": mismatch}

    if rule.get("requires_current_base"):
        if not claim.get("current_base_commit"):
            return {"verdict": "REFUSED", "code": MISSING_PRECONDITION,
                    "detail": "LAND requires current_base_commit"}
        if claim.get("base_commit") != claim.get("current_base_commit"):
            return {"verdict": "REFUSED", "code": STALE_BASE,
                    "detail": "the frozen candidate base no longer equals the current target"}

    return {"verdict": PERMITTED, "code": None,
            "detail": f"{operation} admits {state} -> {rule['to']}"}


def cmd_show(_args: argparse.Namespace) -> int:
    print(json.dumps(load_contract(), indent=2, sort_keys=True))
    return 0


def cmd_judge(args: argparse.Namespace) -> int:
    claim = json.loads(Path(args.claim).read_text(encoding="utf-8"))
    result = evaluate(load_contract(), claim)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verdict"] == PERMITTED else 1


def cmd_selfcheck(_args: argparse.Namespace) -> int:
    contract = load_contract()
    corpus = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    failures = []
    for case in corpus["cases"]:
        result = evaluate(contract, case["claim"])
        observed = result["verdict"] if result["verdict"] == PERMITTED else result["code"]
        if observed != case["expect"]:
            failures.append(f"{case['id']}: expected {case['expect']}, observed {observed}")
    if failures:
        print("FAIL: repository candidate lifecycle")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print(f"PASS: repository candidate lifecycle ({len(corpus['cases'])} cases)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="print the lifecycle contract")
    judge = sub.add_parser("judge", help="grade one JSON transition claim")
    judge.add_argument("claim")
    sub.add_parser("selfcheck", help="prove positive and defeating lifecycle cases")
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 2
    return {"show": cmd_show, "judge": cmd_judge, "selfcheck": cmd_selfcheck}[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
