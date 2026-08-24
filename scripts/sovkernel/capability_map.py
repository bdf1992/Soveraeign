"""Build and check the capability map: every service operation, its office, its door.

``contracts/capability-map.schema.json`` owns the record shape.
``contracts/capability-offices.json`` owns the policy: which office and counter an
operation is met at, what grant it needs, what it may consume, and which transports
are operator-facing or external. This module owns only the derivation from those two
inputs and the rules a schema cannot express, all of which compare the map against
the service manifests it claims to project.

The map is a projection. It is rebuilt from the manifests and the table alone, it
carries the digest of those inputs, and nothing here is authoritative: a row states
which grant an operation requires, never that any actor holds one. An endpoint cannot
carry authority because the schema admits no field for it, so a transport is a way in
and never a second authority path.

Standing vocabulary belongs to ``contracts/service-manifest.schema.json`` and is not
restated here. A row copies whatever standing its manifest declares, so a manifest
that has drifted stays visible in the map instead of being unrepresentable; a standing
this module does not recognise as built simply never opens a door.

A service may also be built in part. Each operation carries its own standing in the
manifest, and each row takes its standing from the operation rather than the service,
because a service-wide standing would either advertise doors that are not there or
hide ones that are.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

MAP_SCHEMA = "soveraeign-capability-map/v1"
BUILT_STANDINGS = ("BUILT", "WITNESSED", "RATIFIED")
IN_PROCESS = "IN_PROCESS"
ACTIVE = "ACTIVE"
DECLARED = "DECLARED_NOT_ACTIVATED"
REFUSED = "REFUSED_UNCONFIGURED"


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def input_state_digest(manifests: dict[str, dict[str, Any]], table: dict[str, Any]) -> str:
    """Digest of everything the map is derived from, so a stale build is detectable."""
    payload = _canonical({"manifests": manifests, "table": table})
    return sha256(payload.encode("utf-8")).hexdigest()


def _endpoints(service_id: str, capability_id: str, standing: str,
               table: dict[str, Any], built: bool) -> list[dict[str, Any]]:
    """One endpoint per declared transport, activated no further than the phase allows.

    A CLI endpoint goes ``ACTIVE`` only for a capability some command actually
    implements. A service owning a CLI does not put every one of its operations
    behind it, and claiming otherwise would be the map advertising a shut door.
    """
    refused = set(table.get("external_transports_refused_in_phase", []))
    cli_command = (table.get("cli_commands") or {}).get(capability_id)
    endpoints: list[dict[str, Any]] = []
    for transport in table.get("transport_policy", {}):
        endpoint: dict[str, Any] = {"transport": transport}
        if transport in refused:
            endpoint["activation"] = REFUSED
            endpoint["refusal_code"] = "UNCONFIGURED"
        elif transport == IN_PROCESS and built:
            endpoint["activation"] = ACTIVE
            endpoint["address"] = f"{service_id}:in-process"
        elif transport == "CLI" and built and cli_command:
            endpoint["activation"] = ACTIVE
            endpoint["address"] = cli_command
        else:
            endpoint["activation"] = DECLARED
        endpoints.append(endpoint)
    return endpoints


def build(manifests: dict[str, dict[str, Any]], table: dict[str, Any], *,
          phase: str, derived_from: list[str], status: str = "PROPOSED") -> dict[str, Any]:
    """Derive the capability map from the service manifests and the office table.

    An operation with no assignment in the table is still emitted, at the ``BACK``
    office with counter ``unassigned``, so an ungoverned door is visible in the map
    rather than missing from it. ``map_defects`` then reports it.
    """
    assignments = table.get("assignments", {})
    capabilities: list[dict[str, Any]] = []
    for service_id in sorted(manifests):
        manifest = manifests[service_id]
        standings = operation_standings(manifest)
        for operation in sorted(standings):
            capability_id = f"{service_id}.{operation}"
            standing = standings[operation]
            built = standing in BUILT_STANDINGS
            endpoints = _endpoints(service_id, capability_id, standing, table, built)
            seat = assignments.get(capability_id, {})
            capabilities.append({
                "capability_id": capability_id,
                "service_id": service_id,
                "operation": operation,
                "office": seat.get("office", "BACK"),
                "counter": seat.get("counter", "unassigned"),
                "service_standing": standing,
                "effect_class": seat.get("effect_class", "RECORD_LOCAL"),
                "required_authority": seat.get("required_authority", "UNASSIGNED"),
                "actor_kinds": list(seat.get("actor_kinds", ["SYSTEM"])),
                "endpoints": [dict(endpoint) for endpoint in endpoints],
            })
    return {
        "map_schema": MAP_SCHEMA,
        "status": status,
        "phase": phase,
        "derived_from": list(derived_from),
        "input_state_digest": input_state_digest(manifests, table),
        "capabilities": capabilities,
    }


def operation_standings(manifest: dict[str, Any]) -> dict[str, str]:
    """Each declared operation id mapped to the standing its manifest gives it.

    A service can be built in part: every operation carries its own standing and only the
    built ones get a live endpoint. A map that marked an unbuilt operation ACTIVE because a
    sibling was built would advertise a door that is not there.
    """
    return {entry["operation"]: entry.get("standing", "PROPOSED")
            for entry in manifest.get("operations", [])}


def _declared_defects(document: dict[str, Any],
                      manifests: dict[str, dict[str, Any]]) -> list[str]:
    """Every row names an operation its service declares, and agrees with it on standing."""
    defects: list[str] = []
    for capability in document.get("capabilities", []):
        label = capability.get("capability_id", "<unnamed>")
        service_id = capability.get("service_id", "")
        manifest = manifests.get(service_id)
        if manifest is None:
            defects.append(f"UNDECLARED_OPERATION: {label} names no service manifest")
            continue
        standings = operation_standings(manifest)
        if capability.get("operation") not in standings:
            defects.append(f"UNDECLARED_OPERATION: {label} is not an operation "
                           f"{service_id} declares")
        expected = standings.get(capability.get("operation"), manifest.get("standing"))
        if capability.get("service_standing") != expected:
            defects.append(f"STANDING_DRIFT: {label} claims "
                           f"{capability.get('service_standing')} while its manifest says "
                           f"{expected}")
    return defects


def _totality_defects(document: dict[str, Any],
                      manifests: dict[str, dict[str, Any]]) -> list[str]:
    """A door the map omits is a door nobody governs, so omission is itself a defect."""
    mapped = {capability.get("capability_id")
              for capability in document.get("capabilities", [])}
    defects: list[str] = []
    for service_id in sorted(manifests):
        for operation in sorted(operation_standings(manifests[service_id])):
            capability_id = f"{service_id}.{operation}"
            if capability_id not in mapped:
                defects.append(f"UNMAPPED_OPERATION: {capability_id} is declared "
                               f"but not mapped")
    return defects


def _office_defects(document: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """Office, counter, and required authority must be the ones the policy table states."""
    counters = table.get("counters", {})
    assignments = table.get("assignments", {})
    defects: list[str] = []
    for capability in document.get("capabilities", []):
        label = capability.get("capability_id", "<unnamed>")
        office = capability.get("office")
        counter = capability.get("counter")
        if counter not in counters.get(office, {}):
            defects.append(f"COUNTER_UNKNOWN: {label} is met at {office}/{counter}, "
                           f"which the office table does not declare")
        seat = assignments.get(label)
        if seat and capability.get("required_authority") != seat.get("required_authority"):
            defects.append(f"AUTHORITY_DRIFT: {label} requires "
                           f"{capability.get('required_authority')!r} in the map and "
                           f"{seat.get('required_authority')!r} in the office table")
    return defects


def _transport_defects(document: dict[str, Any], table: dict[str, Any]) -> list[str]:
    """No serving before BUILT, and no external transport in a phase that refuses it."""
    policy = table.get("transport_policy", {})
    refused = set(table.get("external_transports_refused_in_phase", []))
    defects: list[str] = []
    for capability in document.get("capabilities", []):
        label = capability.get("capability_id", "<unnamed>")
        built = capability.get("service_standing") in BUILT_STANDINGS
        for endpoint in capability.get("endpoints", []):
            transport = endpoint.get("transport")
            activation = endpoint.get("activation")
            if activation == ACTIVE and not built:
                defects.append(f"SERVED_BEFORE_BUILT: {label} serves {transport} while its "
                               f"service stands at {capability.get('service_standing')}")
            if transport in refused and activation != REFUSED:
                defects.append(f"EXTERNAL_TRANSPORT_ACTIVATED: {label} carries {transport} "
                               f"as {activation}, which this phase refuses")
            if (capability.get("office") == "BACK" and activation == ACTIVE
                    and policy.get(transport, {}).get("operator_facing")):
                defects.append(f"BACK_OFFICE_EXPOSED: {label} is back-office work served "
                               f"on the operator-facing transport {transport}")
    return defects


def map_defects(document: dict[str, Any], manifests: dict[str, dict[str, Any]],
                table: dict[str, Any]) -> list[str]:
    """Every rule the schema cannot express. Empty means admissible, never correct."""
    return (_declared_defects(document, manifests)
            + _totality_defects(document, manifests)
            + _office_defects(document, table)
            + _transport_defects(document, table))


def is_stale(document: dict[str, Any], manifests: dict[str, dict[str, Any]],
             table: dict[str, Any]) -> bool:
    """True when the inputs have moved past the build this document records."""
    return document.get("input_state_digest") != input_state_digest(manifests, table)
