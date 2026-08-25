"""Compile service manifests into one machine-readable Kernel binding closure.

The service manifests are already the authored declarations of how each service
participates in the Shared Kernel: record kinds it owns, Kernel contracts it uses,
operations it exposes, named Kernel transitions it realizes, ports it crosses, and
behaviors it forbids. This module does not add a second authored binding file.

Instead it derives a closure over every service manifest plus the authored Kernel
transition table. The closure is useful for discovery, AI context, and conformance:
it answers which service owns a type, which operations realize a transition, and
which declared operations are not yet mapped to a named Kernel traversal.

Nothing here grants authority, promotes standing, settles an operation, or makes the
Kernel a service. ``SPEC.md`` and the governing contracts remain authoritative; this
is a rebuildable projection over their participants.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any
import json

CLOSURE_SCHEMA = "soveraeign-kernel-closure/v1"


def _canonical(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def input_state_digest(manifests: dict[str, dict[str, Any]],
                       transitions: dict[str, Any]) -> str:
    """Digest exactly the authored inputs from which the closure is rebuilt."""
    payload = _canonical({"manifests": manifests, "transitions": transitions})
    return sha256(payload.encode("utf-8")).hexdigest()


def load_manifests(root: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Load every declared service manifest without a hard-coded service list.

    The path is part of the binding identity: ``services/asset/...`` declaring
    ``service_id: registry`` is visible as a defect rather than silently becoming
    Registry merely because JSON said so.
    """
    manifests: dict[str, dict[str, Any]] = {}
    sources: list[str] = []
    for path in sorted((root / "services").glob("*/contracts/service.json")):
        manifest = json.loads(path.read_text(encoding="utf-8"))
        directory_id = path.parents[1].name
        key = directory_id
        manifests[key] = manifest
        sources.append(path.relative_to(root).as_posix())
    return manifests, sources


def build(manifests: dict[str, dict[str, Any]], transitions: dict[str, Any], *,
          derived_from: list[str], status: str = "PROPOSED") -> dict[str, Any]:
    """Derive the Node-wide service-to-Kernel closure.

    Repetition is intentional only in the derived output. Authored facts remain in
    service manifests; the closure normalizes them for machines and can always be
    discarded and rebuilt.
    """
    participants: list[dict[str, Any]] = []
    owners: dict[str, set[str]] = {}
    transition_users: dict[str, list[str]] = {}
    unmapped: list[str] = []

    for directory_id in sorted(manifests):
        manifest = manifests[directory_id]
        service_id = manifest.get("service_id", directory_id)
        operations: list[dict[str, Any]] = []

        for owned_type in manifest.get("owns", []):
            owners.setdefault(owned_type, set()).add(service_id)

        for operation in sorted(manifest.get("operations", []),
                                key=lambda entry: entry.get("operation", "")):
            operation_id = operation.get("operation", "")
            capability_id = f"{service_id}.{operation_id}"
            binding: dict[str, Any] = {
                "capability_id": capability_id,
                "operation": operation_id,
                "logical_endpoint": operation.get("logical_endpoint", ""),
                "subject": operation.get("subject", ""),
                "crud": operation.get("crud", ""),
            }
            transition = operation.get("kernel_transition")
            if transition:
                binding["kernel_transition"] = transition
                transition_users.setdefault(transition, []).append(capability_id)
            else:
                unmapped.append(capability_id)
            operations.append(binding)

        participants.append({
            "service_id": service_id,
            "standing": manifest.get("standing", "PROPOSED"),
            "owns": sorted(manifest.get("owns", [])),
            "kernel_contracts": sorted(manifest.get("uses_kernel_contracts", [])),
            "operations": operations,
            "ports": sorted(manifest.get("ports", [])),
            "depends_on": sorted(manifest.get("depends_on", [])),
            "forbids": sorted(manifest.get("forbids", [])),
        })

    type_ownership = [
        {"type": kind, "owners": sorted(service_ids)}
        for kind, service_ids in sorted(owners.items())
    ]
    transition_usage = [
        {"transition": transition, "operations": sorted(operation_ids)}
        for transition, operation_ids in sorted(transition_users.items())
    ]

    return {
        "closure_schema": CLOSURE_SCHEMA,
        "status": status,
        "derived_from": list(derived_from),
        "input_state_digest": input_state_digest(manifests, transitions),
        "participants": participants,
        "type_ownership": type_ownership,
        "transition_usage": transition_usage,
        "unmapped_operations": sorted(unmapped),
    }


def binding_defects(manifests: dict[str, dict[str, Any]],
                    transitions: dict[str, Any]) -> list[str]:
    """Cross-manifest contradictions a per-file schema cannot express.

    An empty result means the declared service bindings compose under the checks we
    currently know how to state. It does not mean the Kernel vocabulary is ratified
    or complete.
    """
    defects: list[str] = []
    known_transitions = {entry.get("transition")
                         for entry in transitions.get("transitions", [])}
    type_owners: dict[str, list[str]] = {}
    endpoints: dict[str, list[str]] = {}

    for directory_id in sorted(manifests):
        manifest = manifests[directory_id]
        service_id = manifest.get("service_id")
        label = service_id or directory_id

        if service_id != directory_id:
            defects.append(
                f"SERVICE_ID_DRIFT: services/{directory_id} declares service_id "
                f"{service_id!r}"
            )

        for owned_type in manifest.get("owns", []):
            type_owners.setdefault(owned_type, []).append(label)

        operation_names: set[str] = set()
        owns = set(manifest.get("owns", []))
        kernel_contracts = set(manifest.get("uses_kernel_contracts", []))
        for operation in manifest.get("operations", []):
            operation_id = operation.get("operation", "")
            capability_id = f"{label}.{operation_id}"

            if operation_id in operation_names:
                defects.append(f"DUPLICATE_OPERATION: {capability_id} is declared more than once")
            operation_names.add(operation_id)

            expected_endpoint = f"sov://{label}/{operation_id}"
            endpoint = operation.get("logical_endpoint")
            endpoints.setdefault(str(endpoint), []).append(capability_id)
            if endpoint != expected_endpoint:
                defects.append(
                    f"ENDPOINT_IDENTITY_DRIFT: {capability_id} declares {endpoint!r}; "
                    f"expected {expected_endpoint!r}"
                )

            subject = operation.get("subject")
            if subject not in owns:
                defects.append(
                    f"FOREIGN_SUBJECT: {capability_id} acts on {subject!r}, which {label} "
                    "does not own"
                )
            for also_read in operation.get("also_reads", []):
                if also_read not in owns:
                    defects.append(
                        f"FOREIGN_READ: {capability_id} also reads {also_read!r}, which "
                        f"{label} does not own"
                    )

            transition = operation.get("kernel_transition")
            if transition and transition not in known_transitions:
                defects.append(
                    f"UNKNOWN_KERNEL_TRANSITION: {capability_id} names {transition!r}"
                )
            if transition and "operation" not in kernel_contracts:
                defects.append(
                    f"TRANSITION_WITHOUT_OPERATION_CONTRACT: {capability_id} maps to "
                    f"{transition!r} but {label} does not bind the operation contract"
                )

    for owned_type, service_ids in sorted(type_owners.items()):
        unique = sorted(set(service_ids))
        if len(unique) > 1:
            defects.append(
                f"MULTIPLE_TYPE_OWNERS: {owned_type} is owned by {', '.join(unique)}"
            )

    for endpoint, capability_ids in sorted(endpoints.items()):
        unique = sorted(set(capability_ids))
        if endpoint and len(unique) > 1:
            defects.append(
                f"DUPLICATE_LOGICAL_ENDPOINT: {endpoint} is declared by {', '.join(unique)}"
            )

    return defects


def closure_defects(document: dict[str, Any], manifests: dict[str, dict[str, Any]],
                    transitions: dict[str, Any], *, derived_from: list[str]) -> list[str]:
    """Check both authored binding semantics and projection fidelity."""
    defects = binding_defects(manifests, transitions)
    expected = build(manifests, transitions, derived_from=derived_from,
                     status=document.get("status", "PROPOSED"))
    if document != expected:
        defects.append("PROJECTION_DRIFT: Kernel closure does not rebuild from authored inputs")
    return defects


def is_stale(document: dict[str, Any], manifests: dict[str, dict[str, Any]],
             transitions: dict[str, Any]) -> bool:
    return document.get("input_state_digest") != input_state_digest(manifests, transitions)
