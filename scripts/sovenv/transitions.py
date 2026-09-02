"""Promotion crossings, append-preserving receipts, and deployment history.

`admit_crossing` is the pure transition model used by focused conformance tests.
Operational callers must establish authority through `sovenv.authority` first;
the package facade deliberately does not expose this lower-level transition.
"""

from __future__ import annotations

from typing import Any

from .errors import EnvironmentRefused
from .state import definition, env_instance, trunk_definition, trunk_instance


def _crossing(
    pattern: dict[str, Any],
    state: dict[str, Any],
    trunk_id: str,
    source_id: str,
    target_id: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    trunk = trunk_instance(state, trunk_id)
    source = env_instance(state, source_id)
    target = env_instance(state, target_id)
    declared = trunk_definition(pattern, trunk["definition_id"])
    for crossing in declared.get("crossings") or []:
        if (
            crossing.get("from") == source["definition_id"]
            and crossing.get("to") == target["definition_id"]
        ):
            return crossing, source, target
    raise EnvironmentRefused(
        f"CROSSING_NOT_DECLARED:{source['definition_id']}->{target['definition_id']}"
    )


def propose_crossing(
    state: dict[str, Any],
    pattern: dict[str, Any],
    *,
    trunk_instance: str,
    source_instance: str,
    target_instance: str,
    revision: str,
    artifact_digest: str,
    config_digest: str,
    actor: str,
    integration_base: str,
    evidence: list[str],
) -> dict[str, Any]:
    crossing, source, target = _crossing(
        pattern, state, trunk_instance, source_instance, target_instance
    )
    missing = sorted(set(crossing.get("evidence") or []) - set(evidence))
    if missing:
        raise EnvironmentRefused("EVIDENCE_MISSING:" + ",".join(missing))
    state["sequence"] += 1
    record = {
        "crossing_id": f"crossing:{state['sequence']}",
        "status": "PROPOSED",
        "trunk_instance": trunk_instance,
        "source_instance": source_instance,
        "target_instance": target_instance,
        "source_definition": source["definition_id"],
        "target_definition": target["definition_id"],
        "revision": revision,
        "artifact_digest": artifact_digest,
        "config_digest": config_digest,
        "actor": actor,
        "integration_base": integration_base,
        "evidence": sorted(evidence),
        "serialization": crossing["serialization"],
        "receipt_ids": [],
        "receipt": None,
    }
    state["crossing_records"].append(record)
    return record


def _record(state: dict[str, Any], crossing_id: str) -> dict[str, Any]:
    record = next(
        (item for item in state["crossing_records"] if item["crossing_id"] == crossing_id),
        None,
    )
    if record is None:
        raise EnvironmentRefused(f"CROSSING_UNKNOWN:{crossing_id}")
    return record


def _receipt(
    state: dict[str, Any],
    record: dict[str, Any],
    outcome: str,
    reason: str | None,
) -> dict[str, Any]:
    state["sequence"] += 1
    receipt = {
        "receipt_id": f"env-receipt:{state['sequence']}",
        "crossing_id": record["crossing_id"],
        "outcome": outcome,
        "reason": reason,
        "actor": record["actor"],
        "witness": record.get("witness"),
        "revision": record["revision"],
        "artifact_digest": record["artifact_digest"],
        "target_instance": record["target_instance"],
    }
    if record.get("authority_grant_id"):
        receipt["authority_grant_id"] = record["authority_grant_id"]
    state.setdefault("receipts", []).append(receipt)
    record.setdefault("receipt_ids", []).append(receipt["receipt_id"])
    record["receipt"] = receipt
    return receipt


def _refuse(
    state: dict[str, Any], record: dict[str, Any], reason: str, witness: str
) -> dict[str, Any]:
    record["status"] = "REFUSED"
    record["witness"] = witness
    _receipt(state, record, "REFUSED", reason)
    return record


def admit_crossing(
    state: dict[str, Any],
    pattern: dict[str, Any],
    crossing_id: str,
    *,
    current_integration_base: str,
    witness: str,
    authority: str | None,
    authority_grant_id: str | None = None,
    accepted: bool | None = None,
) -> dict[str, Any]:
    """Apply already-established authority to the pure crossing state machine."""
    record = _record(state, crossing_id)
    if record["status"] != "PROPOSED":
        raise EnvironmentRefused("CROSSING_NOT_PROPOSED")
    if record["integration_base"] != current_integration_base:
        return _refuse(state, record, "STALE_ADMISSION_BASE", witness)
    if witness == record["actor"]:
        return _refuse(state, record, "SELF_WITNESS_FORBIDDEN", witness)

    target = definition(pattern, record["target_definition"])
    if target["acceptance"] == "EXPLICIT" and accepted is not True:
        return _refuse(state, record, "EXPLICIT_ACCEPTANCE_REQUIRED", witness)
    if authority not in set(target.get("required_authority") or []):
        return _refuse(state, record, "REQUIRED_AUTHORITY_MISSING", witness)

    if record["serialization"] == "INTEGRATION":
        conflict = next(
            (
                item
                for item in state["crossing_records"]
                if item is not record
                and item["trunk_instance"] == record["trunk_instance"]
                and item["target_instance"] == record["target_instance"]
                and item["status"] == "ADMITTED"
            ),
            None,
        )
        if conflict:
            return _refuse(state, record, "INTEGRATION_CROSSING_BUSY", witness)

    record["status"] = "ADMITTED"
    record["witness"] = witness
    record["authority"] = authority
    if authority_grant_id:
        record["authority_grant_id"] = authority_grant_id
    _receipt(state, record, "ADMITTED", None)
    return record


def land_crossing(
    state: dict[str, Any], crossing_id: str, *, landing_revision: str
) -> dict[str, Any]:
    record = _record(state, crossing_id)
    if record["status"] != "ADMITTED":
        raise EnvironmentRefused("CROSSING_NOT_ADMITTED")
    if landing_revision != record["revision"]:
        record["status"] = "REFUSED"
        _receipt(state, record, "REFUSED", "CANDIDATE_IDENTITY_CHANGED")
        return record
    state["sequence"] += 1
    deployment = {
        "deployment_id": f"deployment:{state['sequence']}",
        "trunk_instance": record["trunk_instance"],
        "environment_instance": record["target_instance"],
        "revision": record["revision"],
        "artifact_digest": record["artifact_digest"],
        "config_digest": record["config_digest"],
        "crossing_id": crossing_id,
        "actor": record["actor"],
        "witness": record["witness"],
        "accepted": True,
    }
    if record.get("authority_grant_id"):
        deployment["authority_grant_id"] = record["authority_grant_id"]
    state["deployments"].append(deployment)
    record["status"] = "LANDED"
    record["deployment_id"] = deployment["deployment_id"]
    _receipt(state, record, "LANDED", None)
    return deployment


def resolve_selector(
    state: dict[str, Any], pattern: dict[str, Any], selector_name: str
) -> dict[str, Any]:
    selector = (pattern.get("selectors") or {}).get(selector_name)
    if selector is None:
        raise EnvironmentRefused(f"SELECTOR_UNKNOWN:{selector_name}")
    definition_id = selector["environment"]
    matching_instances = {
        item["instance_id"]
        for item in state["environment_instances"]
        if item["definition_id"] == definition_id
    }
    history = [
        item
        for item in state["deployments"]
        if item["accepted"] and item["environment_instance"] in matching_instances
    ]
    offset = selector["offset"]
    if len(history) <= offset:
        raise EnvironmentRefused(f"SELECTOR_HISTORY_INSUFFICIENT:{selector_name}")
    return history[-1 - offset]
