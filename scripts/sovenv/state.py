"""Environment instances, trunks, and workspace-binding projections."""

from __future__ import annotations

from typing import Any

from .errors import EnvironmentRefused
from .pattern import digest, validate_pattern


def new_state(pattern: dict[str, Any]) -> dict[str, Any]:
    defects = validate_pattern(pattern)
    if defects:
        raise EnvironmentRefused("; ".join(defects))
    return {
        "schema": "soveraeign-local-environment-state/v1",
        "pattern_id": pattern["id"],
        "pattern_digest": digest(pattern),
        "environment_instances": [],
        "trunk_instances": [],
        "workspace_bindings": [],
        "crossing_records": [],
        "deployments": [],
        "receipts": [],
        "sequence": 0,
    }


def definition(pattern: dict[str, Any], definition_id: str) -> dict[str, Any]:
    for item in pattern.get("environment_definitions") or []:
        if item.get("id") == definition_id:
            return item
    raise EnvironmentRefused(f"ENVIRONMENT_DEFINITION_UNKNOWN:{definition_id}")


def instantiate_environment(
    state: dict[str, Any],
    pattern: dict[str, Any],
    definition_id: str,
    instance_id: str,
) -> dict[str, Any]:
    declared = definition(pattern, definition_id)
    if any(item["instance_id"] == instance_id for item in state["environment_instances"]):
        raise EnvironmentRefused(f"ENVIRONMENT_INSTANCE_DUPLICATE:{instance_id}")
    if declared["multiplicity"] == "ONE" and any(
        item["definition_id"] == definition_id for item in state["environment_instances"]
    ):
        raise EnvironmentRefused(f"ENVIRONMENT_MULTIPLICITY_EXCEEDED:{definition_id}")
    record = {"instance_id": instance_id, "definition_id": definition_id}
    state["environment_instances"].append(record)
    return record


def instantiate_trunk(
    state: dict[str, Any],
    pattern: dict[str, Any],
    definition_id: str,
    instance_id: str,
) -> dict[str, Any]:
    if not any(item.get("id") == definition_id for item in pattern.get("trunk_definitions") or []):
        raise EnvironmentRefused(f"TRUNK_DEFINITION_UNKNOWN:{definition_id}")
    if any(item["instance_id"] == instance_id for item in state["trunk_instances"]):
        raise EnvironmentRefused(f"TRUNK_INSTANCE_DUPLICATE:{instance_id}")
    record = {"instance_id": instance_id, "definition_id": definition_id}
    state["trunk_instances"].append(record)
    return record


def _lease_identity(lease: dict[str, Any]) -> tuple[str, str, str, int]:
    if lease.get("lease_schema") != "soveraeign-work-lease/v1":
        raise EnvironmentRefused("WORK_LEASE_SCHEMA_UNSUPPORTED")
    lease_id = str(lease.get("lease_id") or "")
    concern = str((lease.get("concern") or {}).get("reference") or "")
    principal = str((lease.get("holder") or {}).get("principal_id") or "")
    fence = lease.get("fence")
    if not lease_id or not concern or not principal or not isinstance(fence, int):
        raise EnvironmentRefused("WORK_LEASE_IDENTITY_INCOMPLETE")
    return lease_id, concern, principal, fence


def bind_workspace(
    state: dict[str, Any],
    lease: dict[str, Any],
    *,
    workspace: str,
    branch: str,
    base_revision: str,
) -> dict[str, Any]:
    """Project an existing HELD WorkLease onto one isolated mutable workspace."""
    if lease.get("state") != "HELD":
        raise EnvironmentRefused("WORK_LEASE_NOT_HELD")
    lease_id, concern, principal, fence = _lease_identity(lease)
    for binding in state["workspace_bindings"]:
        if binding["status"] != "ACTIVE":
            continue
        if binding["workspace"] == workspace and binding["lease_id"] != lease_id:
            raise EnvironmentRefused("WORKSPACE_ALREADY_LEASED")
        if binding["lease_id"] == lease_id:
            if binding["fence"] >= fence:
                raise EnvironmentRefused("STALE_LEASE")
            binding["status"] = "SUPERSEDED"
            binding["superseded_by_fence"] = fence
    record = {
        "lease_id": lease_id,
        "concern": concern,
        "principal_id": principal,
        "fence": fence,
        "workspace": workspace,
        "branch": branch,
        "base_revision": base_revision,
        "status": "ACTIVE",
    }
    state["workspace_bindings"].append(record)
    return record


def release_workspace(
    state: dict[str, Any],
    lease: dict[str, Any],
    *,
    reason: str,
) -> dict[str, Any]:
    """Project terminal lease state onto its current workspace binding."""
    if lease.get("state") == "HELD":
        raise EnvironmentRefused("WORK_LEASE_STILL_HELD")
    lease_id, _, _, fence = _lease_identity(lease)
    active = [
        item
        for item in state["workspace_bindings"]
        if item["lease_id"] == lease_id and item["status"] == "ACTIVE"
    ]
    if not active:
        raise EnvironmentRefused("WORKSPACE_BINDING_NOT_ACTIVE")
    current = max(active, key=lambda item: item["fence"])
    if fence < current["fence"]:
        raise EnvironmentRefused("STALE_LEASE")
    current["status"] = "RELEASED"
    current["release_reason"] = reason
    current["release_fence"] = fence
    return current


def env_instance(state: dict[str, Any], instance_id: str) -> dict[str, Any]:
    for item in state["environment_instances"]:
        if item["instance_id"] == instance_id:
            return item
    raise EnvironmentRefused(f"ENVIRONMENT_INSTANCE_UNKNOWN:{instance_id}")


def trunk_instance(state: dict[str, Any], instance_id: str) -> dict[str, Any]:
    for item in state["trunk_instances"]:
        if item["instance_id"] == instance_id:
            return item
    raise EnvironmentRefused(f"TRUNK_INSTANCE_UNKNOWN:{instance_id}")


def trunk_definition(pattern: dict[str, Any], definition_id: str) -> dict[str, Any]:
    for item in pattern.get("trunk_definitions") or []:
        if item.get("id") == definition_id:
            return item
    raise EnvironmentRefused(f"TRUNK_DEFINITION_UNKNOWN:{definition_id}")
