"""Judge one work lease and its subordinates against the constraints a schema cannot state.

``contracts/work-lease.schema.json`` owns the shape of a lease. This module owns the
relations between leases, which is where the interesting refusals live: a helper cannot
be granted more than the parent that recruited it, cannot outlive it, and cannot witness
the work it helped build; a parent cannot declare closure while a child is still holding
part of the concern.

Every refusal code here is either already in the repository's vocabulary or new and
declared. ``STALE_LEASE`` and ``SELF_WITNESS_REFUSED`` are reused deliberately rather
than restated under new names: ``AGENTS.md`` forbids synonyms for existing refusal terms,
and a fencing token here means exactly what it means in
``scripts/sovkernel/transitions.py``.

Nothing in this module grants anything. A lease that passes every check has established
that its holder is attributable and bounded, which is not the same as permitted; the
grant carries that, and a lease with a null grant is an ordinary, admissible lease that
simply cannot reach past the local record.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, NamedTuple

#: Effect classes, weakest first. A child may sit at or below its parent, never above.
EFFECT_ORDER = ("RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD")

#: Relations that answer to a parent lease.
SUBORDINATE = ("HELPER", "WITNESS")

#: States in which a lease is still possessed by its holder.
OPEN_STATES = ("HELD",)

REFUSALS = {
    "STALE_LEASE": "The fence presented was superseded, or the lease had already expired.",
    "SELF_WITNESS_REFUSED": "The witness principal is the principal that built the work.",
    "UNANCHORED_HOLDER": "A non-root holder names no controller principal.",
    "HELPER_WITHOUT_PARENT": "A subordinate lease names no parent lease, or names one "
                             "that was not supplied.",
    "AUTHORITY_WIDENED": "A subordinate lease carries authority its parent does not hold.",
    "LEASE_OUTLIVES_PARENT": "A subordinate lease expires after the parent that recruited it.",
    "CLOSURE_WITH_HELD_CHILD": "A parent declared closure while a child still held part of "
                               "the concern.",
    "CLOSURE_WITHOUT_EVIDENCE": "A completed lease produced no closure evidence.",
    "UNWITNESSED_STANDING_CLAIM": "Closure claims WITNESSED with no witness lease by a "
                                  "different principal.",
    "EFFECT_CLASS_REFUSED": "The declared effect ceiling is above what the current phase "
                            "admits.",
}


class Defect(NamedTuple):
    """One named refusal, with the sentence a reader needs to act on it."""

    code: str
    message: str


def _parse(stamp: str) -> datetime:
    """Read an RFC 3339 timestamp, tolerating the trailing Z this repository writes."""
    return datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))


def _effect_rank(effect: str) -> int:
    return EFFECT_ORDER.index(effect) if effect in EFFECT_ORDER else len(EFFECT_ORDER)


def supersedes(current_fence: int | None, presented_fence: int) -> bool:
    """Whether a presented fence is still the live one.

    A fencing token is not a lock and does not need to be: whoever holds the newest fence
    holds the lease, and an older holder that wakes up late finds its writes refused
    instead of racing. Same rule, same code, as the kernel transition evaluator.
    """
    if current_fence is None:
        return True
    return presented_fence >= current_fence


def _check_holder(lease: dict[str, Any]) -> list[Defect]:
    """Every non-root holder answers to somebody one step up."""
    holder = lease.get("holder", {})
    defects: list[Defect] = []
    if holder.get("controller_principal") is None and holder.get("relation") != "PARENT":
        defects.append(Defect(
            "UNANCHORED_HOLDER",
            f"{lease.get('lease_id')} is held by {holder.get('principal_id')} as "
            f"{holder.get('relation')} with no controller principal; only a root principal "
            f"has nothing above it, and a recruited one is never the root"))
    return defects


def _check_expiry(lease: dict[str, Any], now: datetime | None) -> list[Defect]:
    """A held lease past its expiry is stale, whatever its stored state says."""
    if now is None or lease.get("state") not in OPEN_STATES:
        return []
    try:
        expires = _parse(lease["expires_at"])
    except (KeyError, ValueError):
        return []
    if expires <= now:
        return [Defect(
            "STALE_LEASE",
            f"{lease['lease_id']} is recorded HELD but expired at {lease['expires_at']}; "
            f"an expired holder is not holding anything")]
    return []


def _check_phase(lease: dict[str, Any], phase_ceiling: str) -> list[Defect]:
    """The phase ceiling binds a lease exactly as it binds a transition."""
    ceiling = lease.get("grant", {}).get("effect_ceiling", "RECORD_LOCAL")
    if _effect_rank(ceiling) > _effect_rank(phase_ceiling):
        return [Defect(
            "EFFECT_CLASS_REFUSED",
            f"{lease['lease_id']} declares an effect ceiling of {ceiling} while the phase "
            f"admits at most {phase_ceiling}")]
    return []


def _check_subordination(lease: dict[str, Any], parent: dict[str, Any] | None) -> list[Defect]:
    """A recruited lease is bounded by the one that recruited it, in every dimension."""
    holder = lease.get("holder", {})
    relation = holder.get("relation")
    if relation not in SUBORDINATE:
        return []
    named = holder.get("parent_lease")
    if not named:
        return [Defect("HELPER_WITHOUT_PARENT",
                       f"{lease['lease_id']} is a {relation} lease naming no parent")]
    if parent is None or parent.get("lease_id") != named:
        return [Defect(
            "HELPER_WITHOUT_PARENT",
            f"{lease['lease_id']} names parent {named}, which was not supplied; a helper "
            f"whose parent cannot be read is a helper nobody is responsible for")]

    defects: list[Defect] = []
    defects.extend(_check_grant_containment(lease, parent))
    defects.extend(_check_lifetime_containment(lease, parent))
    if relation == "WITNESS" and holder.get("principal_id") == parent.get(
            "holder", {}).get("principal_id"):
        defects.append(Defect(
            "SELF_WITNESS_REFUSED",
            f"{lease['lease_id']} would have {holder['principal_id']} witness work it holds "
            f"under {parent['lease_id']}; a build cannot witness itself"))
    return defects


def _check_grant_containment(lease: dict[str, Any], parent: dict[str, Any]) -> list[Defect]:
    """The whole point of the subordinate relation: recruiting cannot mint authority.

    An agent may ask for helpers. It may not hand them anything it was not itself given,
    which is what stops a bounded worker from manufacturing an unbounded one and calling
    the result delegation.
    """
    child = lease.get("grant", {})
    above = parent.get("grant", {})
    defects: list[Defect] = []

    widened = sorted(set(child.get("capabilities", [])) - set(above.get("capabilities", [])))
    if widened:
        defects.append(Defect(
            "AUTHORITY_WIDENED",
            f"{lease['lease_id']} carries {', '.join(widened)}, which {parent['lease_id']} "
            f"does not hold; a lease cannot hand on what it was never given"))
    if _effect_rank(child.get("effect_ceiling", "RECORD_LOCAL")) > _effect_rank(
            above.get("effect_ceiling", "RECORD_LOCAL")):
        defects.append(Defect(
            "AUTHORITY_WIDENED",
            f"{lease['lease_id']} declares effect ceiling "
            f"{child.get('effect_ceiling')} above the parent's "
            f"{above.get('effect_ceiling')}"))
    if child.get("authority_type") and child["authority_type"] != above.get("authority_type"):
        defects.append(Defect(
            "AUTHORITY_WIDENED",
            f"{lease['lease_id']} claims {child['authority_type']} authority while "
            f"{parent['lease_id']} holds {above.get('authority_type')}"))
    return defects


def _check_lifetime_containment(lease: dict[str, Any], parent: dict[str, Any]) -> list[Defect]:
    """A helper that outlives its parent is an orphan with a grant."""
    try:
        child_end = _parse(lease["expires_at"])
        parent_end = _parse(parent["expires_at"])
    except (KeyError, ValueError):
        return []
    if child_end > parent_end:
        return [Defect(
            "LEASE_OUTLIVES_PARENT",
            f"{lease['lease_id']} expires at {lease['expires_at']}, after "
            f"{parent['lease_id']} expires at {parent['expires_at']}; nobody would be "
            f"responsible for it in between")]
    return []


def _check_closure(lease: dict[str, Any], children: list[dict[str, Any]]) -> list[Defect]:
    """Closure belongs to the parent, and it is not reached by asserting it.

    Two separate claims live in a completed lease. That the work is done is the holder's,
    and reaches BUILT. That it has been checked is somebody else's, and reaches WITNESSED
    only through a witness lease held by a different principal.
    """
    if lease.get("state") != "COMPLETED":
        return []
    defects: list[Defect] = []
    evidence = lease.get("closure_evidence")
    if not evidence or not evidence.get("evidence_addresses"):
        defects.append(Defect(
            "CLOSURE_WITHOUT_EVIDENCE",
            f"{lease['lease_id']} is COMPLETED with no closure evidence; a lease that "
            f"closes itself on its own say-so has recorded an opinion, not a result"))
        return defects

    still_held = [child["lease_id"] for child in children if child.get("state") in OPEN_STATES]
    if still_held:
        defects.append(Defect(
            "CLOSURE_WITH_HELD_CHILD",
            f"{lease['lease_id']} declares closure while {', '.join(still_held)} still hold "
            f"part of the concern; recruiting help does not move responsibility for closing"))

    if evidence.get("standing_reached") == "WITNESSED":
        witnesses = [child for child in children
                     if child.get("holder", {}).get("relation") == "WITNESS"
                     and child.get("holder", {}).get("principal_id")
                     != lease.get("holder", {}).get("principal_id")]
        if not witnesses:
            defects.append(Defect(
                "UNWITNESSED_STANDING_CLAIM",
                f"{lease['lease_id']} claims WITNESSED with no witness lease held by a "
                f"principal other than {lease.get('holder', {}).get('principal_id')}"))
    return defects


def evaluate(lease: dict[str, Any], *, parent: dict[str, Any] | None = None,
             children: Iterable[dict[str, Any]] = (), now: datetime | None = None,
             phase_ceiling: str = "RESOURCE_CONSUMPTION") -> list[Defect]:
    """Every defect this lease carries, given what it was recruited by and what it recruited.

    ``parent`` is the lease named by a HELPER or WITNESS holder; ``children`` are the leases
    naming this one. Both are supplied by the caller rather than looked up, so this module
    stays a judgement over records and never becomes a second store.

    An empty list means the lease is well-formed and bounded. It does not mean the work is
    done, correct, witnessed, or admitted.
    """
    children = list(children)
    defects: list[Defect] = []
    defects.extend(_check_holder(lease))
    defects.extend(_check_expiry(lease, now))
    defects.extend(_check_phase(lease, phase_ceiling))
    defects.extend(_check_subordination(lease, parent))
    defects.extend(_check_closure(lease, children))
    return defects


def evaluate_set(leases: Iterable[dict[str, Any]], *, now: datetime | None = None,
                 phase_ceiling: str = "RESOURCE_CONSUMPTION") -> dict[str, list[Defect]]:
    """Judge a whole family of leases, resolving parent and child edges from the set itself."""
    by_id = {lease["lease_id"]: lease for lease in leases}
    children: dict[str, list[dict[str, Any]]] = {}
    for lease in by_id.values():
        named = lease.get("holder", {}).get("parent_lease")
        if named:
            children.setdefault(named, []).append(lease)
    return {
        lease_id: evaluate(lease,
                           parent=by_id.get(lease.get("holder", {}).get("parent_lease") or ""),
                           children=children.get(lease_id, []),
                           now=now, phase_ceiling=phase_ceiling)
        for lease_id, lease in by_id.items()
    }
