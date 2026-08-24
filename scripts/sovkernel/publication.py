"""Check a public projection against the records it claims to be derived from.

``contracts/public-projection.schema.json`` owns the view's shape. This module owns
what a shape cannot state: that every entry resolves to a source the projection
declared, that a filtered rebuild says it filtered, that nothing from another node
appears without an admitted crossing, and that a seat this node does not hold did not
publish on its behalf.

The rule doing the work is the third. A public surface is the one place a node's
records are read by people who are not members of it, so an entry that came from
somewhere the node never admitted is the whole boundary failing at once. Checking it
needs the crossing register, which is why this module reads one rather than trusting
the entry's own claim about where it came from.

Nothing here publishes, renders, serves, or reaches a network.
"""

from __future__ import annotations

from typing import Any


def _admitted_origins(crossings: list[dict[str, Any]], node_id: str) -> set[str]:
    """Nodes whose records this node has actually admitted, plus itself.

    An outbound crossing admits nothing here, and an unsettled or refused inbound
    crossing admitted nothing either. Only a settled inbound admission counts.
    """
    origins = {node_id}
    for crossing in crossings:
        admission = crossing.get("admission")
        if crossing.get("to_node") != node_id or not admission:
            continue
        if admission.get("outcome") in ("COMMITTED", "COUNTERED"):
            origins.add(crossing["from_node"])
    return origins


def _source_defects(projection: dict[str, Any]) -> list[str]:
    """Every entry resolves to a declared source, at the digest the source carries."""
    sources = {item["address"]: item["digest"] for item in projection["source_addresses"]}
    defects: list[str] = []
    for entry in projection["entries"]:
        address = entry["thread_address"]
        if address not in sources:
            defects.append(f"entry {address}: not among the declared source_addresses, so the "
                           "view renders a value that resolves to no record")
        elif sources[address] != entry["thread_digest"]:
            defects.append(f"entry {address}: digest {entry['thread_digest']} does not match "
                           f"the declared source digest {sources[address]}")
    return defects


def _omission_defects(projection: dict[str, Any]) -> list[str]:
    """A rebuild that left something out says so."""
    rendered = len(projection["entries"])
    available = len(projection["source_addresses"])
    if rendered < available and not projection["omissions"]:
        return [f"projection renders {rendered} of {available} declared sources and declares "
                "no omissions; a silent filter misrepresents what the node holds"]
    return []


def _origin_defects(projection: dict[str, Any], admitted: set[str]) -> list[str]:
    """Nothing reaches the public surface from a node this one never admitted."""
    defects: list[str] = []
    for entry in projection["entries"]:
        origin = entry["origin_node"]
        if origin not in admitted:
            defects.append(f"entry {entry['thread_address']}: originates in {origin}, which "
                           "this node has not admitted through a settled crossing")
    return defects


def _publisher_defects(projection: dict[str, Any], seats: set[str]) -> list[str]:
    """Publishing is an outward effect, attributable to a seat this node holds."""
    defects: list[str] = []
    for entry in projection["entries"]:
        if entry["published_by"] not in seats:
            defects.append(f"entry {entry['thread_address']}: published by "
                           f"{entry['published_by']}, which is not a seat in this node's "
                           "topology")
    return defects


def projection_defects(projection: dict[str, Any], crossings: list[dict[str, Any]],
                       topology: dict[str, Any]) -> list[str]:
    """Every way this public projection contradicts the node that published it.

    ``projection`` is shaped by ``contracts/public-projection.schema.json``,
    ``crossings`` by ``contracts/federation-crossing.schema.json``, and ``topology``
    by ``contracts/seat-registry.schema.json``. An empty result means the view is
    derived from records the node holds; it says nothing about whether publishing
    any of them was wise.
    """
    node_id = projection["node_id"]
    seats = {seat["seat_id"] for seat in topology.get("seats", [])}
    admitted = _admitted_origins(crossings, node_id)
    return (_source_defects(projection)
            + _omission_defects(projection)
            + _origin_defects(projection, admitted)
            + _publisher_defects(projection, seats))
