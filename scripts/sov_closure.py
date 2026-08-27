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

``selfcheck`` grades the declared corpus in
``conformance/fixtures/closure/handoff-cases.json``; every refusal code in the
contract has at least one case proving it fires. ``judge`` grades one claim
file. ``loop`` prints the declared loop for a participant that wants to read
it. Nothing here contacts a network, writes standing, or grants anything.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "closure-ownership.json"
CORPUS = ROOT / "conformance" / "fixtures" / "closure" / "handoff-cases.json"

PERMITTED = "PERMITTED"
REFUSED = "REFUSED"


def load_contract(path: Path = CONTRACT) -> dict:
    """Read the declared closure-ownership table."""
    return json.loads(path.read_text(encoding="utf-8"))


def _helper(claim: dict) -> dict:
    return claim.get("helper") or {}


def _wip_exceeded(claim: dict, table: dict) -> str | None:
    open_concerns = claim.get("open_unlanded_concerns")
    if open_concerns is None:
        return None
    ceiling = table["wip_policy"]["max_unlanded_concerns_per_participant"]
    if open_concerns > ceiling:
        return f"{open_concerns} unlanded concerns against a ceiling of {ceiling}"
    return None


def _absorbable_follow_on(claim: dict, table: dict) -> str | None:
    follow_on = claim.get("follow_on")
    if not follow_on:
        return None
    predicates = table["absorption_test"]["predicates"]
    if all(follow_on.get(name) for name in predicates):
        return "crosses no service, effect class, or authority boundary"
    return None


def _helper_as_witness(claim: dict, _table: dict) -> str | None:
    helper = _helper(claim)
    if helper.get("role") == "editing" and helper.get("offered_as_witness"):
        return "an editing helper is inside the build and cannot be its independent observation"
    return None


def _routine_decision(claim: dict, table: dict) -> str | None:
    asks = (claim.get("asks") or "").strip().lower()
    for routine in table["routine_decisions"]:
        if asks == routine.lower():
            return f"{routine!r} is the participant's own to settle"
    return None


def _seam_undeclared(claim: dict, table: dict) -> str | None:
    seam = claim.get("seam")
    if not seam:
        return "no seam is named"
    if seam not in table["admissible_seams"]:
        return f"{seam} is not one of {', '.join(sorted(table['admissible_seams']))}"
    return None


def _judgement_not_owner(claim: dict, _table: dict) -> str | None:
    if claim.get("provision") == "judgement" and claim.get("requested_from") != "owner":
        return f"judgement asked of {claim.get('requested_from')!r}"
    return None


def _provision_unrouted(claim: dict, table: dict) -> str | None:
    seam = table["admissible_seams"][claim["seam"]]
    provision = claim.get("provision")
    if provision not in seam["provisions"]:
        return f"{claim['seam']} cannot ask for {provision!r}"
    asked = claim.get("requested_from")
    if asked not in seam["requested_from"]:
        return f"{claim['seam']} cannot be served by {asked!r}"
    return None


def _reachable_alternative(claim: dict, _table: dict) -> str | None:
    alternative = claim.get("reachable_alternative")
    if alternative != "NONE":
        return f"a reachable route forward: {alternative}"
    return None


def _helper_not_recruited(claim: dict, table: dict) -> str | None:
    if claim.get("provision") != "observation":
        return None
    if _helper(claim).get("recruited"):
        return None
    recruit_tool = _step_tool(table, "recruit_helper")
    if recruit_tool in claim.get("tools_available", []):
        return "a helper was recruitable and was not recruited"
    return None


def _step_tool(table: dict, step_name: str) -> str:
    for step in table["loop"]:
        if step["step"] == step_name:
            return step["tool"]
    raise KeyError(step_name)


def _loop_incomplete(claim: dict, table: dict) -> str | None:
    taken = claim.get("loop_steps_taken", [])
    available = claim.get("tools_available", [])
    for step in table["loop"]:
        if not step["required"] or step["step"] in taken:
            continue
        if step["tool"] in available:
            return f"{step['step']!r} was skipped while {step['tool']!r} was available"
    return None


def _recruitment_unbounded(claim: dict, table: dict) -> str | None:
    spent = _helper(claim).get("invocations")
    if spent is None:
        return None
    recruitment = table["helper_policy"]["recruitment"]
    ceiling = recruitment["per_concern_ceiling"]
    if spent <= ceiling or _helper(claim).get("resource_commitment_accepted"):
        return None
    return (f"{spent} helper invocations against a per-concern ceiling of {ceiling},"
            f" with no accepted {recruitment['above_ceiling_reason']}")


def _host_limit_as_owner_question(claim: dict, _table: dict) -> str | None:
    helper = _helper(claim)
    if not (helper.get("blocked_by_host") and helper.get("capability_requested")):
        return None
    if claim.get("requested_from") != "owner" or claim.get("provision") != "judgement":
        return None
    return "the host withheld the helper tool; a missing capability is not an owner ruling"


RULES = {
    "WIP_EXCEEDED": _wip_exceeded,
    "ABSORBABLE_FOLLOW_ON": _absorbable_follow_on,
    "HELPER_AS_WITNESS": _helper_as_witness,
    "RECRUITMENT_UNBOUNDED": _recruitment_unbounded,
    "HOST_LIMIT_AS_OWNER_QUESTION": _host_limit_as_owner_question,
    "ROUTINE_DECISION": _routine_decision,
    "SEAM_UNDECLARED": _seam_undeclared,
    "JUDGEMENT_NOT_OWNER": _judgement_not_owner,
    "PROVISION_UNROUTED": _provision_unrouted,
    "REACHABLE_ALTERNATIVE": _reachable_alternative,
    "HELPER_NOT_RECRUITED": _helper_not_recruited,
    "LOOP_INCOMPLETE": _loop_incomplete,
}


def judge(claim: dict, table: dict | None = None) -> dict:
    """Grade one handoff claim and return its verdict.

    Returns ``{"verdict": PERMITTED}`` or ``{"verdict": REFUSED, "refusal":
    <code>, "because": <reason>}``. The first refusal in the contract's
    declared evaluation order is the one reported.
    """
    table = table or load_contract()
    for code in table["evaluation_order"]:
        because = RULES[code](claim, table)
        if because:
            return {"verdict": REFUSED, "refusal": code, "because": because,
                    "means": table["refusals"][code]}
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
    covered = {c["refusal"] for c in corpus["cases"] if c["expect"] == REFUSED}
    for code in table["refusals"]:
        if code not in covered:
            defects.append(f"{code}: declared in the contract with no case proving it fires")
    return defects


def _cmd_selfcheck(_args: argparse.Namespace) -> int:
    defects = selfcheck()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    for defect in defects:
        print(f"DEFECT {defect}")
    if defects:
        return 1
    print(f"closure ownership: {len(corpus['cases'])} declared cases judged as declared")
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
    return 0 if verdict["verdict"] == PERMITTED else 1


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

    show = subparsers.add_parser("loop", help="print the declared closure loop")
    show.set_defaults(func=_cmd_loop)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
