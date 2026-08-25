"""Resolve one unit of consumption upward through every intention that contains it.

One run can serve a capability that a journey crosses, that serves three promises, one of
which is composed by a compound promise, all of which derive from ground claims. That is
five or six true statements about one expenditure. It is still one expenditure.

This module keeps two things apart:

``DIRECT``
    what a unit of work actually served: exactly one capability. This is what was
    measured.

``ROLLUP``
    every broader intention that contains it. This is a view, and views overlap.

The measured total is computed once, from the set of distinct units, and never by summing
views. Summing the promise views to get a total would count a unit once per promise it
supports, which is how a node ends up reporting that it spent four times what it spent.
``overlap()`` exists so that difference is reportable rather than silent.

No arithmetic here crosses a dimension. Tokens are added to tokens and seconds to seconds;
nothing converts one into the other or into money, because that conversion is policy and
this repository has not declared one.
"""

from __future__ import annotations

from typing import Any, Iterable

#: What a unit of work directly served. Measured once.
DIRECT = "DIRECT"
#: A broader intention that contains it. Viewable through, never summed across.
ROLLUP = "ROLLUP"

#: The dimensions a usage record may carry. USAGE only: BUDGET is an envelope, COST is a
#: valuation of usage, and EFFORT is activity attributable to an objective. Each is a
#: different measurement and none of them belongs in this record (CANON.md, resource
#: words).
DIMENSIONS = frozenset({"wallclock_seconds", "tokens", "tool_calls", "usd"})

#: The levels a unit can be viewed through, innermost first.
LEVELS = ("capability", "journey", "promise", "ground")


class UnknownDimension(ValueError):
    """A usage record carried a dimension the resource vocabulary does not declare."""


def _check_dimensions(unit: dict[str, Any]) -> None:
    unknown = sorted(set(unit["consumed"]) - DIMENSIONS)
    if unknown:
        raise UnknownDimension(
            f"{unit['unit_id']} records {', '.join(unknown)}; usage carries only "
            f"{', '.join(sorted(DIMENSIONS))}. BUDGET, COST and EFFORT are different "
            f"measurements and do not belong in a usage record")


def capability_ancestors(canon: dict[str, Any], capability_id: str) -> dict[str, list[str]]:
    """Every intention that contains one capability, at each level.

    A promise reached only because it composes another promise that a journey serves is
    still a true ancestor: that is what composition means. It is listed once.
    """
    promises = {promise["promise_id"]: promise for promise in canon["promises"]}
    journeys = [journey for journey in canon["journeys"]
                if capability_id in journey["capabilities"]]

    served: set[str] = set()
    for journey in journeys:
        served.update(journey["serves"])
    reached = set(served)
    for promise_id, promise in promises.items():
        if set(promise.get("composes", [])) & served:
            reached.add(promise_id)

    ground: set[str] = set()
    for promise_id in reached:
        ground.update(promises[promise_id]["derives_from"])

    return {
        "capability": [capability_id],
        "journey": sorted(journey["journey_id"] for journey in journeys),
        "promise": sorted(reached),
        "ground": sorted(ground),
    }


def _add(into: dict[str, float], consumed: dict[str, float]) -> None:
    for dimension, amount in consumed.items():
        into[dimension] = into.get(dimension, 0) + amount


def rollup(canon: dict[str, Any], units: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Measure once, then view through every level.

    ``units`` are usage records: ``{unit_id, directly_serves, consumed}``. ``consumed``
    carries usage dimensions only.
    """
    units = list(units)
    measured: dict[str, float] = {}
    seen: set[str] = set()
    views: dict[str, dict[str, dict[str, Any]]] = {level: {} for level in LEVELS}
    unattributed: list[str] = []

    for unit in units:
        _check_dimensions(unit)
        if unit["unit_id"] in seen:
            raise ValueError(f"{unit['unit_id']} appears twice; a unit of consumption is "
                             f"measured once")
        seen.add(unit["unit_id"])
        _add(measured, unit["consumed"])

        ancestors = capability_ancestors(canon, unit["directly_serves"])
        if not ancestors["journey"]:
            unattributed.append(unit["unit_id"])
        for level in LEVELS:
            for identifier in ancestors[level]:
                bucket = views[level].setdefault(identifier, {"units": [], "consumed": {}})
                if unit["unit_id"] in bucket["units"]:
                    continue
                bucket["units"].append(unit["unit_id"])
                _add(bucket["consumed"], unit["consumed"])

    return {
        "measured": measured,
        "unit_count": len(units),
        "attributed": len(units) - len(unattributed),
        "unattributed": unattributed,
        "views": views,
    }


def overlap(result: dict[str, Any], level: str) -> dict[str, float]:
    """How much summing this level's views would over-count, per dimension.

    Zero means the views happen to partition the units at this level. Anything else is the
    amount a naive sum would invent, and it is normal rather than a defect: one run really
    does serve several promises. The defect would be reporting the sum as a total.
    """
    summed: dict[str, float] = {}
    for bucket in result["views"][level].values():
        _add(summed, bucket["consumed"])
    return {dimension: summed.get(dimension, 0) - amount
            for dimension, amount in result["measured"].items()}


def double_counting_defects(result: dict[str, Any], claimed_total: dict[str, float],
                            level: str) -> list[str]:
    """Refuse a total that was reached by summing a level's views."""
    found = []
    for dimension, amount in claimed_total.items():
        if amount != result["measured"].get(dimension, 0):
            found.append(
                f"DOUBLE_COUNTED_USAGE: a total of {amount} {dimension} was claimed while "
                f"{result['measured'].get(dimension, 0)} was measured; summing the "
                f"{level} views counts a unit once per intention it supports, and one "
                f"expenditure that serves several intentions still happened once")
    return found
