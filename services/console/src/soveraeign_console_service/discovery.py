"""Answer a participant asking what it can do here, from the capability projection.

`GROUND-006` says what may be asked of a node is discoverable from the artifact alone,
and `JOURNEY-02` is the journey that realizes it. The answer is built here from
`contracts/fixtures/capability-map.reference.json` - the projection the repository already
rebuilds and checks - so that discovery cannot drift from what the node actually declares.
A hand-maintained list beside the map would answer faster and be wrong the first time an
operation moved.

Two readings, and they are not the same reading:

``available``
    what exists on this node. Every declared operation, with where it can be reached,
    what authority it costs, what it must be given, and how it refuses.

``permitted``
    what this participant may currently do. Computed from live grants, and honest about
    its edges: this service reads one authority store, so it can only speak for the
    capabilities that store governs.

Nothing here grants anything, and a row appearing in ``available`` says only that the node
declares the operation. Whether it runs is what ``endpoints`` reports, and whether it runs
for you is what ``authority`` reports.
"""

from __future__ import annotations

from typing import Any

from soveraeign_console_service.authority import ENFORCED_AUTHORITY
from soveraeign_console_service.core import ConsoleService
from soveraeign_console_service.refusals import StaleCapabilityMap

#: What the two readings mean, carried in the response so a caller cannot mistake one for
#: the other by reading only the numbers.
AVAILABLE = "what exists on this node"
PERMITTED = "what this participant may currently do"

#: How a capability's authority reads for one participant.
HELD = "HELD"
NOT_HELD = "NOT_HELD"
#: Another service's authority store governs this capability. This console does not read
#: it and will not guess.
NOT_KNOWN_HERE = "NOT_KNOWN_HERE"
#: This service governs the capability and the authority name it declares is not the
#: authority name it enforces, so no grant can be matched against it honestly.
UNDETERMINABLE = "UNDETERMINABLE"
#: This service governs the capability, it is built and callable, and it checks no
#: authority at all. A grant is beside the point: any caller is admitted. Distinct from
#: `NOT_KNOWN_HERE`, which means nobody here can answer, and from `NOT_HELD`, which means
#: a check exists and this participant fails it.
NOT_ENFORCED = "NOT_ENFORCED"

ACTIVE = "ACTIVE"
BUILT = "BUILT"


def _reachable(row: dict[str, Any]) -> list[dict[str, Any]]:
    return [endpoint for endpoint in row["endpoints"]
            if endpoint["activation"] == ACTIVE]


def _authority(row: dict[str, Any], service_id: str, enforced: dict[str, str],
               live: dict[str, list[str]] | None) -> dict[str, Any]:
    """How this capability's authority reads for the participant, or why it cannot."""
    declared = row["required_authority"]
    capability_id = row["capability_id"]
    if row["service_id"] != service_id:
        return {"required": declared, "reading": NOT_KNOWN_HERE,
                "because": f"{row['service_id']} keeps its own authority store; this "
                           f"service reads only its own and does not guess at another's"}
    enforcement = enforced.get(capability_id)
    if enforcement is None and row["service_standing"] == BUILT:
        return {"required": declared, "reading": NOT_ENFORCED,
                "because": f"this operation is built and callable, declares {declared!r} "
                           f"and checks nothing; any caller is admitted, so holding a "
                           f"grant makes no difference to whether it runs"}
    if enforcement is None:
        return {"required": declared, "reading": NOT_KNOWN_HERE,
                "because": f"this operation is declared at {row['service_standing']} and "
                           f"has no implementation to enforce anything yet"}
    if enforcement != declared:
        return {"required": declared, "enforced": enforcement, "reading": UNDETERMINABLE,
                "because": f"the office table declares {declared!r} and this service "
                           f"checks {enforcement!r}; a grant cannot be matched against a "
                           f"name the check does not use"}
    if live is None:
        return {"required": declared, "reading": NOT_KNOWN_HERE,
                "because": "no participant was named, so no grant was read"}
    scopes = live.get(declared, [])
    if scopes:
        return {"required": declared, "reading": HELD, "scopes": sorted(scopes)}
    return {"required": declared, "reading": NOT_HELD,
            "because": "no live grant in this journal names that capability"}


def _row(row: dict[str, Any], service_id: str, enforced: dict[str, str],
         live: dict[str, list[str]] | None) -> dict[str, Any]:
    """One capability, with everything a fresh participant needs to decide about it."""
    active = _reachable(row)
    shape = row.get("shape", {})
    return {
        "capability_id": row["capability_id"],
        "service_id": row["service_id"],
        "operation": row["operation"],
        "logical_endpoint": shape.get("logical_endpoint"),
        "standing": row["service_standing"],
        "office": f"{row['office']}/{row['counter']}",
        "actor_kinds": list(row["actor_kinds"]),
        "effect_class": row["effect_class"],
        "reachable": bool(active),
        "endpoints": [dict(endpoint) for endpoint in row["endpoints"]],
        "authority": _authority(row, service_id, enforced, live),
        "acts_on": shape.get("subject"),
        "crud": shape.get("crud"),
        "requirement": shape.get("requirement"),
        "kernel_transition": shape.get("kernel_transition"),
        "preconditions": list(shape.get("preconditions", [])),
        "commits": shape.get("commit"),
        "refusals": list(shape.get("refusals", [])),
    }


def _live_grants(grants: list[dict[str, Any]] | None) -> dict[str, list[str]] | None:
    if grants is None:
        return None
    live: dict[str, list[str]] = {}
    for grant in grants:
        live.setdefault(grant["capability"], []).append(grant["scope"])
    return live


def operations(capability_map: dict[str, Any], *, service_id: str = "console",
               enforced: dict[str, str] | None = None,
               grants: list[dict[str, Any]] | None = None,
               operator_id: str | None = None,
               fresh: bool | None = None) -> dict[str, Any]:
    """What can be asked of this node, and what this participant may currently ask.

    ``fresh`` is the caller's answer to the ``capability_map_fresh`` precondition the
    manifest declares. This service reads the projection and cannot rebuild it, so it
    refuses an answer the caller has established is stale, and says plainly when nobody
    checked rather than implying somebody did.
    """
    if fresh is False:
        raise StaleCapabilityMap(
            "the capability map is behind its sources; rebuild it with "
            "`python scripts/sov_capability.py build` before asking what can be done")
    enforced = enforced or {}
    live = _live_grants(grants)
    rows = [_row(row, service_id, enforced, live)
            for row in capability_map["capabilities"]]

    readings = {}
    for row in rows:
        readings.setdefault(row["authority"]["reading"], []).append(row["capability_id"])

    omissions = [
        "a row here says the node declares the operation, never that it works",
        "reachability is what the projection recorded, not a call that succeeded",
    ]
    if UNDETERMINABLE in readings:
        omissions.append(
            f"{len(readings[UNDETERMINABLE])} capability(s) declare one authority name and "
            f"enforce another, so no grant can be matched against them honestly")
    if NOT_ENFORCED in readings:
        omissions.append(
            f"{len(readings[NOT_ENFORCED])} capability(s) are built, declare an authority "
            f"and check none: {', '.join(sorted(readings[NOT_ENFORCED]))}. Any caller is "
            f"admitted to those regardless of what they hold")
    if NOT_KNOWN_HERE in readings:
        omissions.append(
            f"{len(readings[NOT_KNOWN_HERE])} capability(s) are governed by an authority "
            f"store this service does not read")

    return {
        "capability_revision": capability_map["input_state_digest"],
        "map_status": capability_map["status"],
        "freshness": {
            "verified": fresh,
            "how": "python scripts/sov_capability.py check",
            "note": "unverified means nobody checked, not that the map is current",
        },
        "readings": {"available": AVAILABLE, "permitted": PERMITTED},
        "operator_id": operator_id,
        "counts": {
            "declared": len(rows),
            "reachable": sum(1 for row in rows if row["reachable"]),
            "authority": {name: len(ids) for name, ids in sorted(readings.items())},
        },
        "operations": rows,
        "authoritative": False,
        "omissions": omissions,
    }


def discover(console: ConsoleService, capability_map: dict[str, Any],
             operator_id: str | None = None,
             fresh: bool | None = None) -> dict[str, Any]:
    """`console.discover-operations`: what this node declares, and what this operator holds.

    Takes the console so the permitted reading is computed from live grants in the
    journal rather than from anything the caller passed in. Naming no operator returns
    the available reading alone, which is a narrower answer rather than a wrong one.
    """
    return operations(
        capability_map,
        enforced=ENFORCED_AUTHORITY,
        grants=console.grants(operator_id) if operator_id is not None else None,
        operator_id=operator_id,
        fresh=fresh)
