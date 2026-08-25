"""Check a node registry against the local seat topology (decisions/0039).

``contracts/node-identity.schema.json`` owns one node record. This module owns the
rules a single record cannot state, because every one of them is a property of the
registry read against the topology it belongs to.

The rule worth naming is the third. A peer's root seat must be absent from the local
seat topology. A peer node is sovereign over itself and settles its own copy of a
crossing; the moment its root seat appears in the local registry, that settlement
authority has been written into this node, and a crossing has become a merge. The
schema cannot see this, because each record is individually well formed.

Nothing here admits a peer, carries a crossing, or reads a message. Passing means the
registry is coherent with the topology, never that any peer is trustworthy.
"""

from __future__ import annotations

from typing import Any

SELF = "SELF"
PEER = "PEER"


def _seat_index(topology: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """seat_id -> seat record, from a seat-registry projection."""
    return {seat["seat_id"]: seat for seat in topology.get("seats", [])}


def _relation_defects(registry: list[dict[str, Any]]) -> list[str]:
    """Exactly one node in a registry is the node that holds it."""
    selves = [node["node_id"] for node in registry if node.get("relation") == SELF]
    if not selves:
        return ["registry: no node declares relation SELF, so nothing holds it"]
    if len(selves) > 1:
        return [f"registry: {len(selves)} nodes declare relation SELF ({', '.join(sorted(selves))}); "
                "a registry is held by one node"]
    return []


def _uniqueness_defects(registry: list[dict[str, Any]]) -> list[str]:
    """Two records for one node_id would give a node two identities at once."""
    defects: list[str] = []
    seen: set[str] = set()
    for node in registry:
        node_id = node["node_id"]
        if node_id in seen:
            defects.append(f"{node_id}: appears more than once in the registry")
        seen.add(node_id)
    return defects


def _self_defects(node: dict[str, Any], seats: dict[str, dict[str, Any]],
                  topology: dict[str, Any]) -> list[str]:
    """The holding node's root seat must be this topology's root seat."""
    label = node["node_id"]
    root = node["root_seat"]
    if root not in seats:
        return [f"{label}: names root seat {root}, which is not a seat in the local topology"]
    if seats[root].get("seat_type") != "root":
        return [f"{label}: names root seat {root}, which is typed "
                f"{seats[root].get('seat_type')!r} and cannot settle"]
    if topology.get("root_seat") != root:
        return [f"{label}: names root seat {root}, but the local topology is rooted at "
                f"{topology.get('root_seat')}"]
    return []


def _peer_defects(node: dict[str, Any], seats: dict[str, dict[str, Any]],
                  topology: dict[str, Any]) -> list[str]:
    """A peer's authority stays in the peer's node; only its identity crosses."""
    label = node["node_id"]
    defects: list[str] = []
    root = node["root_seat"]
    if root in seats:
        defects.append(
            f"{label}: its root seat {root} appears in the local seat topology; a peer settles "
            "in its own node, so admitting its root seat here turns a crossing into a merge"
        )
    admitted_by = node["admitted_by"]
    if admitted_by not in seats:
        defects.append(f"{label}: admitted_by {admitted_by} is not a seat in the local topology")
    elif admitted_by != topology.get("root_seat"):
        defects.append(
            f"{label}: admitted by {admitted_by}, but admitting a peer is a judgement and the "
            f"local topology is rooted at {topology.get('root_seat')}"
        )
    return defects


def registry_defects(registry: list[dict[str, Any]], topology: dict[str, Any]) -> list[str]:
    """Every way this node registry contradicts the seat topology it belongs to.

    ``registry`` is a list of records shaped by ``contracts/node-identity.schema.json``;
    ``topology`` is a projection shaped by ``contracts/seat-registry.schema.json``. An
    empty result means the registry is coherent, not that any peer in it is sound.
    """
    seats = _seat_index(topology)
    defects = _relation_defects(registry) + _uniqueness_defects(registry)
    for node in registry:
        if node.get("relation") == SELF:
            defects.extend(_self_defects(node, seats, topology))
        else:
            defects.extend(_peer_defects(node, seats, topology))
    return defects
