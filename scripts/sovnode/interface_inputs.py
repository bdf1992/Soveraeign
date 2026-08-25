"""Load and check every source used to rebuild the Node Interface projection."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from sovkernel.capability_map import is_stale as capability_stale
from sovkernel.capability_map import map_defects
from sovkernel.closure_inputs import rebuild as rebuild_closure
from sovkernel.jsonschema import validate
from sovkernel.kernel_binding import (
    binding_defects,
    load_source_digests,
)
from sovkernel.node_identity import registry_defects
from sovkernel.node_interface import build as build_interface
from sovkernel.node_interface import interface_defects
from sovnode.composition import route_census

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "contracts" / "fixtures" / "node-interface.reference.json"
SCHEMA = ROOT / "contracts" / "node-interface.schema.json"


def _load(root: Path, address: str) -> Any:
    return json.loads((root / address).read_text("utf-8"))


def _holder_defects(registry: dict[str, Any]) -> list[str]:
    selves = [node for node in registry.get("nodes", []) if node.get("relation") == "SELF"]
    if len(selves) != 1:
        return [f"NODE_HOLDER_INVALID: expected one SELF node, found {len(selves)}"]
    if registry.get("self_node") != selves[0].get("node_id"):
        return ["NODE_HOLDER_INVALID: self_node does not name the SELF record"]
    return []


def rebuild(root: Path = ROOT) -> tuple[dict[str, Any], list[str]]:
    """Rebuild from current sources; no checked-in projection is trusted as input."""
    (closure, manifests, transitions, paradigms,
     closure_sources, closure_source_defects) = rebuild_closure(root)
    closure_addresses = [entry["address"] for entry in closure_sources]
    routes = route_census()
    addresses = set(closure_addresses)
    addresses.update({
        "contracts/capability-offices.json",
        "contracts/fixtures/capability-map.reference.json",
        "contracts/fixtures/node-registry.reference.json",
        "contracts/fixtures/seat-topology.reference.json",
        "bindings/console/interface.json",
    })
    for route in routes:
        addresses.update(route["source_addresses"])
    source_digests, source_defects = load_source_digests(root, sorted(addresses))
    capability = _load(root, "contracts/fixtures/capability-map.reference.json")
    offices = _load(root, "contracts/capability-offices.json")
    registry = _load(root, "contracts/fixtures/node-registry.reference.json")
    topology = _load(root, "contracts/fixtures/seat-topology.reference.json")
    human_interface = _load(root, "bindings/console/interface.json")
    observations: dict[str, list[str]] = {}

    defects = list(closure_source_defects) + list(source_defects)
    defects.extend(binding_defects(manifests, transitions, paradigms))
    defects.extend(validate(closure, _load(root, "contracts/kernel-closure.schema.json")))
    defects.extend(validate(capability, _load(root, "contracts/capability-map.schema.json")))
    defects.extend(map_defects(capability, manifests, offices))
    if capability_stale(capability, manifests, offices):
        defects.append("CAPABILITY_MAP_STALE: authored inputs moved past the projection")
    node_schema = _load(root, "contracts/node-identity.schema.json")
    for node in registry.get("nodes", []):
        defects.extend(f"NODE_CONTRACT: {item}" for item in validate(node, node_schema))
    defects.extend(_holder_defects(registry))
    defects.extend(registry_defects(registry.get("nodes", []), topology))
    if defects:
        return {}, defects

    document = build_interface(
        registry, topology, closure, capability, manifests, routes,
        human_interface, observations, source_digests)
    defects.extend(interface_defects(document, closure, routes, observations))
    if SCHEMA.exists():
        defects.extend(validate(document, _load(root, "contracts/node-interface.schema.json")))
    return document, defects


__all__ = ["REFERENCE", "ROOT", "SCHEMA", "rebuild"]
