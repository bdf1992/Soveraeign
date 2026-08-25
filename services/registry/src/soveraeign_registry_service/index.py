"""Build a disposable operation index without redefining its sources."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json


class RegistryIndexError(ValueError):
    """The supplied projections and authored sources do not compose exactly."""


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return sha256(_canonical(value).encode("utf-8")).hexdigest()


def _manifest_operations(manifests: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    operations: dict[str, dict[str, Any]] = {}
    for service_id, manifest in manifests.items():
        if manifest.get("service_id") != service_id:
            raise RegistryIndexError(f"service identity drift for {service_id}")
        for operation in manifest.get("operations", []):
            capability_id = f"{service_id}.{operation.get('operation', '')}"
            if capability_id in operations:
                raise RegistryIndexError(f"duplicate operation {capability_id}")
            operations[capability_id] = operation
    return operations


def build_operation_index(
        closure: dict[str, Any], manifests: dict[str, dict[str, Any]],
        policy: dict[str, Any], source_digests: list[dict[str, str]]) -> tuple[
            dict[str, dict[str, Any]], str]:
    """Index closure operation identities and point every answer back to sources."""
    details = _manifest_operations(manifests)
    assignments = policy.get("assignments", {})
    digests = {item["address"]: item["digest"] for item in source_digests}
    policy_address = "contracts/capability-offices.json"
    if policy_address not in digests:
        raise RegistryIndexError("capability policy has no addressed source digest")

    aliases: dict[str, dict[str, Any]] = {}
    seen_capabilities: set[str] = set()
    for participant in closure.get("participants", []):
        service_id = participant.get("service_id", "")
        manifest_address = f"services/{service_id}/contracts/service.json"
        if manifest_address not in digests:
            raise RegistryIndexError(f"{service_id} manifest has no source digest")
        for binding in participant.get("operations", []):
            capability_id = binding.get("capability_id", "")
            endpoint = binding.get("logical_endpoint", "")
            detail = details.get(capability_id)
            assignment = assignments.get(capability_id)
            if detail is None or not isinstance(assignment, dict):
                raise RegistryIndexError(f"{capability_id} has no authored detail or policy")
            if detail.get("logical_endpoint") != endpoint:
                raise RegistryIndexError(f"{capability_id} endpoint differs from its manifest")
            if capability_id in seen_capabilities:
                raise RegistryIndexError(f"duplicate closure operation {capability_id}")
            seen_capabilities.add(capability_id)
            entry = {
                "kind": "operation",
                "name": endpoint,
                "capability_id": capability_id,
                "service_id": service_id,
                "standing": detail.get("standing", "PROPOSED"),
                "kernel_paradigms": list(participant.get("kernel_contracts", [])),
                "kernel_transition": binding.get("kernel_transition"),
                "office": assignment.get("office"),
                "required_authority": assignment.get("required_authority"),
                "effect_class": assignment.get("effect_class"),
                "actor_kinds": list(assignment.get("actor_kinds", [])),
                "sources": [
                    {"address": manifest_address, "digest": digests[manifest_address]},
                    {"address": policy_address, "digest": digests[policy_address]},
                ],
                "standing_effect": "NONE",
            }
            entry["record_digest"] = _digest(entry)
            for alias in (endpoint, capability_id):
                if not alias or alias in aliases:
                    raise RegistryIndexError(f"registry name collision for {alias!r}")
                aliases[alias] = entry

    if set(details) != seen_capabilities:
        missing = sorted(set(details) - seen_capabilities)
        raise RegistryIndexError(f"closure omits manifest operations: {missing}")
    input_digest = _digest({
        "closure_input_state_digest": closure.get("input_state_digest"),
        "source_digests": source_digests,
        "entries": sorted({item["record_digest"] for item in aliases.values()}),
    })
    return aliases, input_digest


__all__ = ["RegistryIndexError", "build_operation_index"]
