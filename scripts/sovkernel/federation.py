"""Check federation crossings against the node registry and seat topology (decisions/0039).

``contracts/federation-crossing.schema.json`` owns one crossing. This module owns the
rules that need the node holding it: which direction the crossing runs, whether this
node may settle it at all, and whose seat produced the offer.

The rule the design rests on is direction. A node may settle a crossing addressed to
it and may not settle one it sent, because the receiving node's judgement is that
node's record. Holding a peer's admission here as settled would be this node claiming
to know how another sovereign node ruled, which is the merge that ``decisions/0039``
says federation avoids by giving every node a root seat that settles its own copy.

Nothing here transports anything, reaches a network, or admits an offer. It reads
records that already exist and reports how they contradict each other.
"""

from __future__ import annotations

from typing import Any

from sovkernel.node_identity import PEER, SELF


def _self_node(registry: list[dict[str, Any]]) -> str | None:
    for node in registry:
        if node.get("relation") == SELF:
            return node["node_id"]
    return None


def _known_nodes(registry: list[dict[str, Any]]) -> set[str]:
    return {node["node_id"] for node in registry}


def _seat_ids(topology: dict[str, Any]) -> set[str]:
    return {seat["seat_id"] for seat in topology.get("seats", [])}


def _direction_defects(crossing: dict[str, Any], holder: str, known: set[str],
                       label: str) -> list[str]:
    """A crossing joins two distinct known nodes, one of which is the holder."""
    origin, target = crossing["from_node"], crossing["to_node"]
    defects: list[str] = []
    if origin == target:
        defects.append(f"{label}: from_node and to_node are both {origin}; a node does not "
                       "cross to itself")
    for role, node_id in (("from_node", origin), ("to_node", target)):
        if node_id not in known:
            defects.append(f"{label}: {role} {node_id} is not in the node registry, so no "
                           "local seat has admitted it")
    if holder not in (origin, target):
        defects.append(f"{label}: runs between {origin} and {target}, neither of which is "
                       f"{holder}; this node is not party to it")
    return defects


def _settlement_defects(crossing: dict[str, Any], holder: str, topology: dict[str, Any],
                        label: str) -> list[str]:
    """Only the receiving node settles, and only its root seat does the settling."""
    admission = crossing.get("admission")
    inbound = crossing["to_node"] == holder
    if not inbound:
        if admission is not None:
            return [f"{label}: {holder} sent this offer and holds a settlement for it; the "
                    "receiving node's judgement is the receiving node's record"]
        return []
    if admission is None:
        return []
    root = topology.get("root_seat")
    if admission["admitted_by"] != root:
        return [f"{label}: settled by {admission['admitted_by']}, but admitting a peer's "
                f"record is a judgement and this node is rooted at {root}"]
    return []


def _origin_seat_defects(crossing: dict[str, Any], holder: str, seats: set[str],
                         label: str) -> list[str]:
    """An inbound offer was produced somewhere else, by a seat that is not ours."""
    origin_seat = crossing["origin_seat"]
    if crossing["from_node"] == holder:
        if origin_seat not in seats:
            return [f"{label}: {holder} sent this offer, but {origin_seat} is not a seat in "
                    "this node's topology"]
        return []
    if origin_seat in seats:
        return [f"{label}: offered by {crossing['from_node']} through {origin_seat}, which is "
                "a seat in this node's own topology; a peer's seat does not exist here"]
    return []


def crossing_defects(crossings: list[dict[str, Any]], registry: list[dict[str, Any]],
                     topology: dict[str, Any]) -> list[str]:
    """Every way these crossings contradict the registry and topology holding them.

    ``crossings`` are records shaped by ``contracts/federation-crossing.schema.json``,
    ``registry`` by ``contracts/node-identity.schema.json``, and ``topology`` by
    ``contracts/seat-registry.schema.json``. An empty result means the crossings are
    coherent, never that an offer is true or that a peer is honest.
    """
    holder = _self_node(registry)
    if holder is None:
        return ["registry: no node declares relation SELF, so no crossing has a holder"]
    known = _known_nodes(registry)
    seats = _seat_ids(topology)
    defects: list[str] = []
    for crossing in crossings:
        label = crossing["crossing_id"]
        defects.extend(_direction_defects(crossing, holder, known, label))
        defects.extend(_settlement_defects(crossing, holder, topology, label))
        defects.extend(_origin_seat_defects(crossing, holder, seats, label))
    return defects


def peers(registry: list[dict[str, Any]]) -> list[str]:
    """Every peer node this registry has admitted, in identifier order."""
    return sorted(node["node_id"] for node in registry if node.get("relation") == PEER)
