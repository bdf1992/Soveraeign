"""Draw against a work lease's budget and report what the drawing looks like.

A budget is an envelope, not a throttle. The purpose stated when this was commissioned is
to make autonomy's operating envelope visible and pathological behaviour observable - a
participant consuming a great deal while producing coordination objects and never
approaching closure. That is a reading this module produces, not a gate it enforces.

Two measurements are kept apart throughout, because they are not the same thing:

``consumption``
    what was spent - wall clock, tokens, tool calls, money, turns, skill invocations.

``emission``
    what was produced - helper leases, witness leases, branches, pull requests, issues,
    external effects. A pull request consumes nothing to hold and still crowds the world.

No arithmetic here crosses a dimension, for the reason ``CANON.md`` gives: this repository
has declared no policy converting tokens into seconds or either into money, so a total
across dimensions would be an invention. ``pressure`` selects the worst single fraction
rather than combining them, which is a comparison, not a sum.
"""

from __future__ import annotations

from typing import Any, Iterable

from sovkernel import attribution

#: Consumption dimensions a lease budget may bound.
DIMENSIONS = frozenset({"wallclock_seconds", "tokens", "tool_calls", "usd",
                        "turns", "skill_invocations"})

#: The subset a receipt can already record. The difference is a real gap, reported as
#: ``UNRECEIPTABLE_USAGE`` rather than papered over by widening the receipt enum here.
RECEIPTABLE = frozenset(attribution.DIMENSIONS)

#: Coordination objects a lease budget may bound.
COUNTERS = frozenset({"helper_leases", "witness_leases", "branches",
                      "pull_requests", "issues", "external_effects"})

#: The fraction of a declared consumption limit past which a lease with no closure evidence
#: and outstanding coordination objects is worth naming. Not a threshold for refusal.
PRESSURE_NOTICE = 0.5


class UnknownDimension(ValueError):
    """A draw named a dimension or counter the lease vocabulary does not declare."""


def _limits(entries: Iterable[dict[str, Any]], key: str) -> dict[str, float]:
    return {entry[key]: entry["limit"] for entry in entries}


def _totals(draws: Iterable[dict[str, Any]], kind: str, key: str,
            allowed: frozenset[str]) -> dict[str, float]:
    """Sum the draws of one kind, per dimension, refusing an undeclared name outright."""
    totals: dict[str, float] = {}
    for draw in draws:
        if draw.get("kind") != kind:
            continue
        name = draw.get(key)
        if name not in allowed:
            raise UnknownDimension(
                f"{draw.get('lease_id')} draws {name!r}, which is not one of "
                f"{', '.join(sorted(allowed))}; a new dimension is a decision record, "
                f"not a new string")
        totals[name] = totals.get(name, 0) + draw["amount"]
    return totals


def account(lease: dict[str, Any], draws: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """What this lease has drawn, what remains, and where it is over.

    ``draws`` are ledger records: ``{lease_id, kind, dimension|counter, amount}``. A
    dimension the budget did not bound is reported under ``unbounded`` rather than
    refused: enumerating every possible limit on every lease would make budgets ceremony,
    and an unbounded dimension that is being drawn is exactly the thing worth seeing.
    """
    draws = [draw for draw in draws if draw.get("lease_id") == lease["lease_id"]]
    budget = lease.get("budget", {})
    consumption_limits = _limits(budget.get("consumption", []), "dimension")
    emission_limits = _limits(budget.get("emission", []), "counter")

    consumed = _totals(draws, "consumption", "dimension", frozenset(DIMENSIONS))
    emitted = _totals(draws, "emission", "counter", frozenset(COUNTERS))

    over: list[dict[str, Any]] = []
    remaining: dict[str, float] = {}
    for name, amount in sorted(consumed.items()):
        if name not in consumption_limits:
            continue
        remaining[name] = consumption_limits[name] - amount
        if amount > consumption_limits[name]:
            over.append({"kind": "consumption", "name": name,
                         "limit": consumption_limits[name], "drawn": amount})
    for name, amount in sorted(emitted.items()):
        if name not in emission_limits:
            continue
        remaining[name] = emission_limits[name] - amount
        if amount > emission_limits[name]:
            over.append({"kind": "emission", "name": name,
                         "limit": emission_limits[name], "drawn": amount})

    unbounded = sorted(
        [name for name in consumed if name not in consumption_limits]
        + [name for name in emitted if name not in emission_limits])
    unreceiptable = sorted(name for name in consumed if name not in RECEIPTABLE)

    return {
        "lease_id": lease["lease_id"],
        "consumed": consumed,
        "emitted": emitted,
        "remaining": remaining,
        "over": over,
        "unbounded": unbounded,
        "unreceiptable": unreceiptable,
    }


def pressure(accounted: dict[str, Any], lease: dict[str, Any]) -> float:
    """The worst single bounded dimension, as a fraction of its limit.

    Selected rather than combined. A lease at 90% of its token budget and 5% of its wall
    clock is a lease at 90%, and adding the two would describe nothing that happened.
    Returns 0.0 when nothing bounded has been drawn.
    """
    limits = _limits(lease.get("budget", {}).get("consumption", []), "dimension")
    limits.update(_limits(lease.get("budget", {}).get("emission", []), "counter"))
    drawn = dict(accounted["consumed"])
    drawn.update(accounted["emitted"])
    fractions = [amount / limits[name] for name, amount in drawn.items()
                 if limits.get(name)]
    return max(fractions) if fractions else 0.0


def readings(lease: dict[str, Any], draws: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Named observations about how this lease is being spent. None of them refuse anything.

    ``COORDINATION_WITHOUT_CLOSURE`` is the one this was commissioned for: a holder well
    into its envelope, having produced coordination objects, with no closure evidence and
    the lease still open. It is a shape worth a human look, not a defect - some work
    genuinely is like that - which is why it is a reading and not a refusal.
    """
    accounted = account(lease, draws)
    found: list[dict[str, Any]] = []

    for item in accounted["over"]:
        found.append({
            "code": "BUDGET_EXCEEDED",
            "message": f"{lease['lease_id']} drew {item['drawn']} {item['name']} against a "
                       f"limit of {item['limit']}"})
    if accounted["unreceiptable"]:
        found.append({
            "code": "UNRECEIPTABLE_USAGE",
            "message": f"{lease['lease_id']} drew "
                       f"{', '.join(accounted['unreceiptable'])}, which no receipt field "
                       f"can carry yet; the budget bounds more than the receipt records"})
    if accounted["unbounded"]:
        found.append({
            "code": "UNBOUNDED_DIMENSION",
            "message": f"{lease['lease_id']} drew {', '.join(accounted['unbounded'])} with "
                       f"no declared limit; consumption without an envelope is not a "
                       f"defect, but nothing here would have noticed it growing"})

    emitted = sum(accounted["emitted"].values())
    closed = bool(lease.get("closure_evidence"))
    if (not closed and lease.get("state") == "HELD" and emitted > 0
            and pressure(accounted, lease) >= PRESSURE_NOTICE):
        found.append({
            "code": "COORDINATION_WITHOUT_CLOSURE",
            "message": f"{lease['lease_id']} is {pressure(accounted, lease):.0%} into its "
                       f"tightest bound and has produced {int(emitted)} coordination "
                       f"object(s), with no closure evidence against "
                       f"'{lease.get('closure', {}).get('condition', 'its closure condition')}'"})
    return found
