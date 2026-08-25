"""Judge the product canon, and trace a journey down to what is reachable today.

``CANON.md`` owns the wording. ``contracts/product-canon.json`` owns the identifiers
and the joins, and this module owns the rules a schema cannot express: that every
promise a journey serves exists, that every capability a journey names is a real
declared operation, that no promise is named and then realized by nothing, and that a
retired identifier never comes back meaning something else.

The trace is the point. A canon that only asserted "this journey serves that promise"
would be a taxonomy. Joining each journey's capabilities against
``contracts/fixtures/capability-map.reference.json`` turns it into a measurement: how
much of a promise is reachable, how much is declared and unreachable, and how much has
no operation behind it at all. The last column is the one the map cannot hold, because
the map is total over what exists and silent about what does not.

Nothing here grants anything. A journey naming a capability does not make it reachable,
and a promise with a full set of active endpoints is still only reachable, never kept.
"""

from __future__ import annotations

from typing import Any

#: What a journey's crossing can be. REACHABLE means some transport is ACTIVE today;
#: DECLARED means the operation exists and no transport carries it; MISSING means no
#: service declares the operation at all.
REACHABLE = "REACHABLE"
DECLARED = "DECLARED_NOT_REACHABLE"
MISSING = "MISSING"


def _capability_rows(capability_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["capability_id"]: row for row in capability_map["capabilities"]}


def _active_transports(row: dict[str, Any]) -> list[str]:
    return [endpoint["transport"] for endpoint in row["endpoints"]
            if endpoint["activation"] == "ACTIVE"]


def defects(canon: dict[str, Any], capability_map: dict[str, Any]) -> list[str]:
    """Every join rule the schema cannot express. Empty means admissible, never correct."""
    found: list[str] = []
    promises = {promise["promise_id"]: promise for promise in canon["promises"]}
    participants = {person["participant_id"] for person in canon["participants"]}
    rows = _capability_rows(capability_map)
    retired = {entry["id"] for entry in canon["retired"]}

    for promise_id in sorted(promises):
        for part in promises[promise_id].get("composes", []):
            if part not in promises:
                found.append(f"UNKNOWN_PROMISE: {promise_id} composes {part}, "
                             f"which this canon does not declare")
            elif part == promise_id:
                found.append(f"SELF_COMPOSING_PROMISE: {promise_id} composes itself")

    served: set[str] = set()
    for journey in canon["journeys"]:
        label = journey["journey_id"]
        if journey["participant"] not in participants:
            found.append(f"UNKNOWN_PARTICIPANT: {label} is walked by "
                         f"{journey['participant']!r}, which this canon does not declare")
        for promise_id in journey["serves"]:
            if promise_id not in promises:
                found.append(f"UNKNOWN_PROMISE: {label} serves {promise_id}, "
                             f"which this canon does not declare")
            else:
                served.add(promise_id)
        for capability_id in journey["capabilities"]:
            if capability_id not in rows:
                found.append(f"UNDECLARED_CAPABILITY: {label} names {capability_id}, "
                             f"which no service manifest declares; a crossing with no "
                             f"operation belongs in missing_capabilities")
        for entry in journey["missing_capabilities"]:
            if entry["name"] in rows:
                found.append(f"MISSING_BUT_DECLARED: {label} records {entry['name']!r} as "
                             f"missing while the capability map declares it")

    for promise_id, promise in sorted(promises.items()):
        if promise_id in served:
            continue
        if any(promise_id in other.get("composes", []) for other in promises.values()):
            continue
        found.append(f"UNREALIZED_PROMISE: {promise_id} is declared and no journey serves it "
                     f"and no promise composes it; a promise nothing reaches is a claim")

    for identifier in sorted(retired):
        if identifier in promises or identifier in {j["journey_id"] for j in canon["journeys"]}:
            found.append(f"RETIRED_IDENTIFIER_REUSED: {identifier} is retired and declared "
                         f"again in the same canon")
    return found


def crossing_states(journey: dict[str, Any],
                    capability_map: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per crossing this journey needs, with what carries it today."""
    rows = _capability_rows(capability_map)
    states: list[dict[str, Any]] = []
    for capability_id in journey["capabilities"]:
        row = rows.get(capability_id)
        if row is None:
            states.append({"crossing": capability_id, "state": MISSING,
                           "because": "named by the canon and declared by no manifest"})
            continue
        active = _active_transports(row)
        states.append({
            "crossing": capability_id,
            "state": REACHABLE if active else DECLARED,
            "transports": active,
            "office": f"{row['office']}/{row['counter']}",
            "authority": row["required_authority"],
            "standing": row["service_standing"],
        })
    for entry in journey["missing_capabilities"]:
        states.append({"crossing": entry["name"], "state": MISSING,
                       "because": entry["because"]})
    return states


def journey_reading(journey: dict[str, Any], capability_map: dict[str, Any]) -> dict[str, Any]:
    """How far this journey gets today, counted rather than described."""
    states = crossing_states(journey, capability_map)
    counts = {REACHABLE: 0, DECLARED: 0, MISSING: 0}
    for state in states:
        counts[state["state"]] += 1
    return {
        "journey_id": journey["journey_id"],
        "title": journey["title"],
        "participant": journey["participant"],
        "serves": list(journey["serves"]),
        "crossings": states,
        "counts": counts,
        "walkable": counts[DECLARED] == 0 and counts[MISSING] == 0,
    }


def promise_reading(canon: dict[str, Any], capability_map: dict[str, Any],
                    promise_id: str) -> dict[str, Any]:
    """Every journey serving one promise, and the totals across them.

    A promise that composes others answers for its parts too: PROMISE-01 is not reachable
    because its own journeys are, but because everything it is made of is.

    The totals count each crossing once. Two journeys serving one promise routinely cross
    the same operation, and summing their counts would report a promise as needing more
    of the node than it does - the same double-counting that makes summing resource views
    wrong (`scripts/sovkernel/attribution.py`). `journey_appearances` keeps the difference
    visible instead of hiding it.
    """
    promises = {promise["promise_id"]: promise for promise in canon["promises"]}
    wanted = {promise_id} | set(promises[promise_id].get("composes", []))
    readings = [journey_reading(journey, capability_map) for journey in canon["journeys"]
                if wanted & set(journey["serves"])]

    distinct: dict[str, str] = {}
    appearances = 0
    for reading in readings:
        for state in reading["crossings"]:
            appearances += 1
            distinct.setdefault(state["crossing"], state["state"])
    totals = {REACHABLE: 0, DECLARED: 0, MISSING: 0}
    for state in distinct.values():
        totals[state] += 1

    return {
        "promise_id": promise_id,
        "statement": promises[promise_id]["statement"],
        "phase": promises[promise_id]["phase"],
        "source": promises[promise_id]["source"],
        "derives_from": list(promises[promise_id]["derives_from"]),
        "composes": list(promises[promise_id].get("composes", [])),
        "journeys": readings,
        "totals": totals,
        "distinct_crossings": len(distinct),
        "journey_appearances": appearances,
    }
