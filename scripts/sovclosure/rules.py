"""The twelve refusal predicates, apart from the CLI that reports them.

One predicate per refusal code declared in ``contracts/closure-ownership.json``.
Each reads a claim and the table and returns the reason it refuses, or ``None``
when it does not fire. None of them holds a copy of the table: a ceiling, a
seam, or a routine decision changes in the contract, not here.

``RULES`` maps a declared refusal code to its predicate. The contract's
``evaluation_order`` decides which one is reported when several would fire.
"""

from __future__ import annotations

from typing import Callable

Predicate = Callable[[dict, dict], "str | None"]


def _helper(claim: dict) -> dict:
    return claim.get("helper") or {}


def _step_tool(table: dict, step_name: str) -> str:
    for step in table["loop"]:
        if step["step"] == step_name:
            return step["tool"]
    raise KeyError(step_name)


def wip_exceeded(claim: dict, table: dict) -> str | None:
    """A second concern opened while the participant's previous one is unlanded."""
    open_concerns = claim.get("open_unlanded_concerns")
    if open_concerns is None:
        return None
    ceiling = table["wip_policy"]["max_unlanded_concerns_per_participant"]
    if open_concerns > ceiling:
        return f"{open_concerns} unlanded concerns against a ceiling of {ceiling}"
    return None


def absorbable_follow_on(claim: dict, table: dict) -> str | None:
    """Filed work that crosses no service, effect class, or authority boundary."""
    follow_on = claim.get("follow_on")
    if not follow_on:
        return None
    predicates = table["absorption_test"]["predicates"]
    if all(follow_on.get(name) for name in predicates):
        return "crosses no service, effect class, or authority boundary"
    return None


def helper_as_witness(claim: dict, _table: dict) -> str | None:
    """An editing helper offered as the independent observation."""
    helper = _helper(claim)
    if helper.get("role") == "editing" and helper.get("offered_as_witness"):
        return "an editing helper is inside the build and cannot be its independent observation"
    return None


def routine_decision(claim: dict, table: dict) -> str | None:
    """Another tier asked to settle something the concern's holder owns."""
    asks = (claim.get("asks") or "").strip().lower()
    for routine in table["routine_decisions"]:
        if asks == routine.lower():
            return f"{routine!r} is the participant's own to settle"
    return None


def seam_undeclared(claim: dict, table: dict) -> str | None:
    """A handoff naming no seam, or one outside the admissible five."""
    seam = claim.get("seam")
    if not seam:
        return "no seam is named"
    if seam not in table["admissible_seams"]:
        return f"{seam} is not one of {', '.join(sorted(table['admissible_seams']))}"
    return None


def judgement_not_owner(claim: dict, _table: dict) -> str | None:
    """Judgement asked of a tier that is not the owner."""
    if claim.get("provision") == "judgement" and claim.get("requested_from") != "owner":
        return f"judgement asked of {claim.get('requested_from')!r}"
    return None


def provision_unrouted(claim: dict, table: dict) -> str | None:
    """A provision the named seam cannot ask for, or a tier that cannot serve it."""
    seam = table["admissible_seams"][claim["seam"]]
    provision = claim.get("provision")
    if provision not in seam["provisions"]:
        return f"{claim['seam']} cannot ask for {provision!r}"
    asked = claim.get("requested_from")
    if asked not in seam["requested_from"]:
        return f"{claim['seam']} cannot be served by {asked!r}"
    return None


def reachable_alternative(claim: dict, _table: dict) -> str | None:
    """An admissible route forward exists, so the concern is gated and not handed off."""
    alternative = claim.get("reachable_alternative")
    if alternative != "NONE":
        return f"a reachable route forward: {alternative}"
    return None


def helper_not_recruited(claim: dict, table: dict) -> str | None:
    """A reading asked of another tier that a recruitable helper could have given."""
    if claim.get("provision") != "observation":
        return None
    if _helper(claim).get("recruited"):
        return None
    recruit_tool = _step_tool(table, "recruit_helper")
    if recruit_tool in claim.get("tools_available", []):
        return "a helper was recruitable and was not recruited"
    return None


def loop_incomplete(claim: dict, table: dict) -> str | None:
    """A required loop step skipped while the tool it needs was available."""
    taken = claim.get("loop_steps_taken", [])
    available = claim.get("tools_available", [])
    for step in table["loop"]:
        if not step["required"] or step["step"] in taken:
            continue
        if step["tool"] in available:
            return f"{step['step']!r} was skipped while {step['tool']!r} was available"
    return None


def recruitment_unbounded(claim: dict, table: dict) -> str | None:
    """Helpers spent past the ceiling and presented as ordinary closure."""
    spent = _helper(claim).get("invocations")
    if spent is None:
        return None
    recruitment = table["helper_policy"]["recruitment"]
    ceiling = recruitment["per_concern_ceiling"]
    if spent <= ceiling or _helper(claim).get("resource_commitment_accepted"):
        return None
    return (f"{spent} helper invocations against a per-concern ceiling of {ceiling},"
            f" with no accepted {recruitment['above_ceiling_reason']}")


def host_limit_as_owner_question(claim: dict, _table: dict) -> str | None:
    """A capability the host withheld routed to the owner as judgement."""
    helper = _helper(claim)
    if not (helper.get("blocked_by_host") and helper.get("capability_requested")):
        return None
    if claim.get("requested_from") != "owner" or claim.get("provision") != "judgement":
        return None
    return "the host withheld the helper tool; a missing capability is not an owner ruling"


RULES: dict[str, Predicate] = {
    "WIP_EXCEEDED": wip_exceeded,
    "ABSORBABLE_FOLLOW_ON": absorbable_follow_on,
    "HELPER_AS_WITNESS": helper_as_witness,
    "RECRUITMENT_UNBOUNDED": recruitment_unbounded,
    "HOST_LIMIT_AS_OWNER_QUESTION": host_limit_as_owner_question,
    "ROUTINE_DECISION": routine_decision,
    "SEAM_UNDECLARED": seam_undeclared,
    "JUDGEMENT_NOT_OWNER": judgement_not_owner,
    "PROVISION_UNROUTED": provision_unrouted,
    "REACHABLE_ALTERNATIVE": reachable_alternative,
    "HELPER_NOT_RECRUITED": helper_not_recruited,
    "LOOP_INCOMPLETE": loop_incomplete,
}
