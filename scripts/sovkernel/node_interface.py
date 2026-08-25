"""Compile the Node's read interface without opening a route or granting authority."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

from sovnode.affordances import defects as affordance_defects
from sovnode.affordances import derive as derive_affordance

INTERFACE_SCHEMA = "soveraeign-node-interface/v1"
ACTIVE = "ACTIVE"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def input_state_digest(source_digests: list[dict[str, str]],
                       routes: list[dict[str, Any]],
                       observations: dict[str, list[str]]) -> str:
    """Digest every addressed input; changing raw source bytes makes the view stale."""
    return _digest({"sources": source_digests, "routes": routes,
                    "observations": observations})


def _operation_index(closure: dict[str, Any]) -> tuple[
        dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    operations: dict[str, dict[str, Any]] = {}
    participants: dict[str, dict[str, Any]] = {}
    for participant in closure.get("participants", []):
        participants[participant["service_id"]] = participant
        for operation in participant.get("operations", []):
            operations[operation["capability_id"]] = operation
    return operations, participants


def _choices(interface: dict[str, Any]) -> dict[str, list[str]]:
    return {
        f"console.{operation['manifest_operation']}": list(
            operation.get("decision_vocabulary", []))
        for operation in interface.get("operations", [])
    }


def _source_records(addresses: set[str], digests: dict[str, str]) -> list[dict[str, str]]:
    return [{"address": address, "digest": digests[address]}
            for address in sorted(addresses) if address in digests]


def _operation_record(capability: dict[str, Any], declaration: dict[str, Any],
                      participant: dict[str, Any], detail: dict[str, Any],
                      routes: list[dict[str, Any]], observations: list[str],
                      paradigms: dict[str, dict[str, Any]], choices: list[str],
                      digests: dict[str, str]) -> dict[str, Any]:
    operation_id = capability["capability_id"]
    active = [dict(endpoint) for endpoint in capability.get("endpoints", [])
              if endpoint.get("activation") == ACTIVE]
    reachability = []
    for route in routes:
        admitted = any(endpoint.get("transport") == route["transport"]
                       and endpoint.get("address") == route["address"] for endpoint in active)
        reachability.append({
            "transport": route["transport"], "address": route["address"],
            "policy_active": admitted,
            "required_arguments": list(route["required_arguments"]),
            "optional_arguments": list(route["optional_arguments"]),
            "source_addresses": list(route["source_addresses"]),
        })
    reachable = any(route["policy_active"] for route in reachability)
    kernel_ids = list(participant.get("kernel_contracts", []))
    kernel_sources = {source for paradigm in kernel_ids
                      for source in paradigms.get(paradigm, {}).get("sources", [])}
    source_addresses = {
        f"services/{capability['service_id']}/contracts/service.json",
        "contracts/fixtures/capability-map.reference.json",
        "contracts/capability-offices.json",
        "contracts/kernel-paradigms.json",
        "contracts/kernel-transitions.json",
        "contracts/node-interface.schema.json",
        "scripts/sovkernel/node_interface.py",
        "scripts/sovnode/affordances.py",
        *kernel_sources,
    }
    for route in routes:
        source_addresses.update(route["source_addresses"])
    if operation_id.startswith("console."):
        source_addresses.add("bindings/console/interface.json")

    record: dict[str, Any] = {
        "operation_id": operation_id,
        "service_id": capability["service_id"],
        "operation": capability["operation"],
        "logical_endpoint": declaration["logical_endpoint"],
        "standing": capability["service_standing"],
        "subject": declaration["subject"],
        "crud": declaration["crud"],
        "commit": detail.get("commit", "UNSTATED"),
        "kernel_paradigms": kernel_ids,
        "kernel_transition": declaration.get("kernel_transition"),
        "required_authority": capability["required_authority"],
        "effect_class": capability["effect_class"],
        "actor_kinds": list(capability["actor_kinds"]),
        "preconditions": list(detail.get("preconditions", [])),
        "refusals": list(detail.get("refusals", [])),
        "legal_choices": choices,
        "policy_endpoints": [dict(endpoint) for endpoint in capability["endpoints"]],
        "reachability": reachability,
        "observation_ids": sorted(observations),
        "facts": {
            "declared": True,
            "bound": True,
            "policy_active": bool(active),
            "reachable": reachable,
            "observed": bool(observations),
        },
        "sources": _source_records(source_addresses, digests),
    }
    record["affordance"] = derive_affordance(record)
    record["record_digest"] = _digest(record)
    return record


def build(node_registry: dict[str, Any], topology: dict[str, Any],
          closure: dict[str, Any], capability_map: dict[str, Any],
          manifests: dict[str, dict[str, Any]], routes: list[dict[str, Any]],
          human_interface: dict[str, Any], observations: dict[str, list[str]],
          source_digests: list[dict[str, str]]) -> dict[str, Any]:
    """Join authored and derived facts while keeping their evidence layers separate."""
    closure_operations, participants = _operation_index(closure)
    paradigms = {item["paradigm"]: item for item in closure["paradigm_usage"]}
    route_index: dict[str, list[dict[str, Any]]] = {}
    for route in routes:
        route_index.setdefault(route["operation_id"], []).append(route)
    choice_index = _choices(human_interface)
    digests = {entry["address"]: entry["digest"] for entry in source_digests}
    details = {f"{service_id}.{operation['operation']}": operation
               for service_id, manifest in manifests.items()
               for operation in manifest.get("operations", [])}

    operations = []
    for capability in capability_map.get("capabilities", []):
        operation_id = capability["capability_id"]
        declaration = closure_operations[operation_id]
        operations.append(_operation_record(
            capability, declaration, participants[capability["service_id"]],
            details[operation_id], route_index.get(operation_id, []),
            observations.get(operation_id, []), paradigms,
            choice_index.get(operation_id, []), digests))

    selves = [node for node in node_registry["nodes"] if node.get("relation") == "SELF"]
    holder = selves[0]
    seams = {
        "built_not_reachable": [item["operation_id"] for item in operations
                                if item["standing"] in ("BUILT", "WITNESSED", "RATIFIED")
                                and not item["facts"]["reachable"]],
        "policy_active_not_reachable": [item["operation_id"] for item in operations
                                        if item["facts"]["policy_active"]
                                        and not item["facts"]["reachable"]],
        "reachable_not_observed": [item["operation_id"] for item in operations
                                   if item["facts"]["reachable"]
                                   and not item["facts"]["observed"]],
        "unmapped_kernel_transition": list(closure["unmapped_operations"]),
    }
    counts = {name: sum(1 for item in operations if item["facts"][name])
              for name in ("declared", "bound", "policy_active", "reachable", "observed")}
    return {
        "interface_schema": INTERFACE_SCHEMA,
        "status": "PROPOSED",
        "node": {
            "node_id": holder["node_id"], "display_name": holder["display_name"],
            "root_seat": holder["root_seat"],
            "node_source": "contracts/fixtures/node-registry.reference.json",
            "root_source": "contracts/fixtures/seat-topology.reference.json",
            "node_source_digest": digests["contracts/fixtures/node-registry.reference.json"],
            "root_source_digest": digests["contracts/fixtures/seat-topology.reference.json"],
        },
        "kernel": {
            "closure_schema": closure["closure_schema"],
            "closure_input_state_digest": closure["input_state_digest"],
            "paradigms": sorted(paradigms),
            "participants": len(participants),
        },
        "derived_from": [entry["address"] for entry in source_digests],
        "source_digests": list(source_digests),
        "input_state_digest": input_state_digest(source_digests, routes, observations),
        "counts": counts,
        "seams": seams,
        "omissions": [
            {
                "code": "OBJECT_INSTANCES_NOT_PROJECTED",
                "explanation": (
                    "Service-owned types and operations are visible; live object instances "
                    "and their current relations are not yet Node Interface inputs."
                ),
            },
            {
                "code": "MODEL_BINDINGS_NOT_PROJECTED",
                "explanation": (
                    "Adapter declarations and recorded model inventories are not Node routes; "
                    "an inventory match cannot expose model invocation here."
                ),
            },
            {
                "code": "HARNESS_STATE_NOT_PROJECTED",
                "explanation": (
                    "Host schedules and workflows are harness plumbing, not governed service state."
                ),
            },
        ],
        "operations": operations,
    }


def interface_defects(document: dict[str, Any], closure: dict[str, Any],
                      routes: list[dict[str, Any]],
                      observations: dict[str, list[str]]) -> list[str]:
    """Cross-input contradictions the Node Interface must not render away."""
    defects: list[str] = []
    operation_ids = [item.get("operation_id") for item in document.get("operations", [])]
    declared, _ = _operation_index(closure)
    if len(operation_ids) != len(set(operation_ids)):
        defects.append("DUPLICATE_OPERATION: Node Interface repeats an operation")
    if set(operation_ids) != set(declared):
        defects.append("OPERATION_CENSUS_DRIFT: interface and Kernel closure differ")
    for route in routes:
        operation_id = route.get("operation_id")
        if operation_id not in declared:
            defects.append(f"UNDECLARED_ROUTE: {operation_id} has no Kernel binding")
        elif route.get("logical_endpoint") != declared[operation_id].get("logical_endpoint"):
            defects.append(f"ROUTE_IDENTITY_DRIFT: {operation_id} changes its endpoint")
    unknown_observations = sorted(set(observations) - set(declared))
    defects.extend(f"OBSERVATION_SUBJECT_UNKNOWN: {item}" for item in unknown_observations)
    for record in document.get("operations", []):
        defects.extend(affordance_defects(record))
    return defects


__all__ = ["build", "input_state_digest", "interface_defects"]
