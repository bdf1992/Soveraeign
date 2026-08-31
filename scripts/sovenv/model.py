"""General local SDLC environment/trunk/deployment kernel.

Environment names are data. The kernel composes existing Soveraeign work leases
and receipts; it does not mint work, authority, approval, or a second queue.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json
import os
import tempfile


class EnvironmentRefused(ValueError):
    """A requested local SDLC transition is not admissible."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + sha256(canonical(value)).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise EnvironmentRefused("DOCUMENT_NOT_OBJECT")
    return value


def validate_pattern(pattern: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if pattern.get("schema") != "soveraeign-environment-pattern/v1":
        defects.append("PATTERN_SCHEMA_UNSUPPORTED")
    definitions = pattern.get("environment_definitions") or []
    ids = [str(item.get("id") or "") for item in definitions]
    if not ids or any(not item for item in ids):
        defects.append("ENVIRONMENT_DEFINITION_ID_REQUIRED")
    if len(ids) != len(set(ids)):
        defects.append("ENVIRONMENT_DEFINITION_DUPLICATE")
    env_ids = set(ids)
    for item in definitions:
        if item.get("multiplicity") not in {"ONE", "MANY"}:
            defects.append(f"ENVIRONMENT_MULTIPLICITY_INVALID:{item.get('id')}")
        if item.get("acceptance") not in {"NONE", "EXPLICIT"}:
            defects.append(f"ENVIRONMENT_ACCEPTANCE_INVALID:{item.get('id')}")

    trunks = pattern.get("trunk_definitions") or []
    trunk_ids: set[str] = set()
    for trunk in trunks:
        trunk_id = str(trunk.get("id") or "")
        if not trunk_id:
            defects.append("TRUNK_ID_REQUIRED")
        elif trunk_id in trunk_ids:
            defects.append(f"TRUNK_DUPLICATE:{trunk_id}")
        trunk_ids.add(trunk_id)
        for crossing in trunk.get("crossings") or []:
            source = crossing.get("from")
            target = crossing.get("to")
            if source not in env_ids or target not in env_ids:
                defects.append(f"CROSSING_ENVIRONMENT_UNKNOWN:{trunk_id}:{source}->{target}")
            if source == target:
                defects.append(f"CROSSING_SELF_LOOP:{trunk_id}:{source}")
            if crossing.get("serialization") not in {"NONE", "INTEGRATION"}:
                defects.append(
                    f"CROSSING_SERIALIZATION_INVALID:{trunk_id}:{source}->{target}"
                )
            if not isinstance(crossing.get("evidence") or [], list):
                defects.append(f"CROSSING_EVIDENCE_INVALID:{trunk_id}:{source}->{target}")
    if not trunks:
        defects.append("TRUNK_DEFINITION_REQUIRED")

    for name, selector in (pattern.get("selectors") or {}).items():
        if selector.get("kind") != "ACCEPTED_HISTORY":
            defects.append(f"SELECTOR_KIND_UNSUPPORTED:{name}")
        if not isinstance(selector.get("offset"), int) or selector.get("offset") < 0:
            defects.append(f"SELECTOR_OFFSET_INVALID:{name}")
        if selector.get("environment") not in env_ids:
            defects.append(f"SELECTOR_ENVIRONMENT_UNKNOWN:{name}")
    return defects


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
        "sequence": 0,
    }


def _definition(pattern: dict[str, Any], definition_id: str) -> dict[str, Any]:
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
    definition = _definition(pattern, definition_id)
    if any(item["instance_id"] == instance_id for item in state["environment_instances"]):
        raise EnvironmentRefused(f"ENVIRONMENT_INSTANCE_DUPLICATE:{instance_id}")
    if definition["multiplicity"] == "ONE" and any(
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


def bind_workspace(
    state: dict[str, Any],
    lease: dict[str, Any],
    *,
    workspace: str,
    branch: str,
    base_revision: str,
) -> dict[str, Any]:
    """Bind an existing HELD WorkLease to an isolated mutable workspace."""
    if lease.get("lease_schema") != "soveraeign-work-lease/v1" or lease.get("state") != "HELD":
        raise EnvironmentRefused("WORK_LEASE_NOT_HELD")
    lease_id = str(lease.get("lease_id") or "")
    concern = str((lease.get("concern") or {}).get("reference") or "")
    principal = str((lease.get("holder") or {}).get("principal_id") or "")
    fence = lease.get("fence")
    if not lease_id or not concern or not principal or not isinstance(fence, int):
        raise EnvironmentRefused("WORK_LEASE_IDENTITY_INCOMPLETE")
    for binding in state["workspace_bindings"]:
        if binding["status"] != "ACTIVE":
            continue
        if binding["workspace"] == workspace and binding["lease_id"] != lease_id:
            raise EnvironmentRefused("WORKSPACE_ALREADY_LEASED")
        if binding["lease_id"] == lease_id and binding["fence"] >= fence:
            raise EnvironmentRefused("STALE_LEASE")
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


def _env_instance(state: dict[str, Any], instance_id: str) -> dict[str, Any]:
    for item in state["environment_instances"]:
        if item["instance_id"] == instance_id:
            return item
    raise EnvironmentRefused(f"ENVIRONMENT_INSTANCE_UNKNOWN:{instance_id}")


def _trunk_instance(state: dict[str, Any], instance_id: str) -> dict[str, Any]:
    for item in state["trunk_instances"]:
        if item["instance_id"] == instance_id:
            return item
    raise EnvironmentRefused(f"TRUNK_INSTANCE_UNKNOWN:{instance_id}")


def _trunk_definition(pattern: dict[str, Any], definition_id: str) -> dict[str, Any]:
    for item in pattern.get("trunk_definitions") or []:
        if item.get("id") == definition_id:
            return item
    raise EnvironmentRefused(f"TRUNK_DEFINITION_UNKNOWN:{definition_id}")


def _crossing(
    pattern: dict[str, Any],
    state: dict[str, Any],
    trunk_instance: str,
    source_instance: str,
    target_instance: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    trunk = _trunk_instance(state, trunk_instance)
    source = _env_instance(state, source_instance)
    target = _env_instance(state, target_instance)
    definition = _trunk_definition(pattern, trunk["definition_id"])
    for crossing in definition.get("crossings") or []:
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
        "receipt": None,
    }
    state["crossing_records"].append(record)
    return record


def admit_crossing(
    state: dict[str, Any],
    pattern: dict[str, Any],
    crossing_id: str,
    *,
    current_integration_base: str,
    witness: str,
    authority: str | None,
    accepted: bool | None = None,
) -> dict[str, Any]:
    record = next(
        (item for item in state["crossing_records"] if item["crossing_id"] == crossing_id),
        None,
    )
    if record is None:
        raise EnvironmentRefused(f"CROSSING_UNKNOWN:{crossing_id}")
    if record["status"] != "PROPOSED":
        raise EnvironmentRefused("CROSSING_NOT_PROPOSED")
    if record["integration_base"] != current_integration_base:
        return _refuse(state, record, "STALE_ADMISSION_BASE", witness)
    if witness == record["actor"]:
        return _refuse(state, record, "SELF_WITNESS_FORBIDDEN", witness)

    target_definition = _definition(pattern, record["target_definition"])
    if target_definition["acceptance"] == "EXPLICIT" and accepted is not True:
        return _refuse(state, record, "EXPLICIT_ACCEPTANCE_REQUIRED", witness)
    if authority not in set(target_definition.get("required_authority") or []):
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
    record["receipt"] = _receipt(state, record, "ADMITTED", None)
    return record


def _receipt(
    state: dict[str, Any],
    record: dict[str, Any],
    outcome: str,
    reason: str | None,
) -> dict[str, Any]:
    state["sequence"] += 1
    return {
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


def _refuse(
    state: dict[str, Any], record: dict[str, Any], reason: str, witness: str
) -> dict[str, Any]:
    record["status"] = "REFUSED"
    record["witness"] = witness
    record["receipt"] = _receipt(state, record, "REFUSED", reason)
    return record


def land_crossing(
    state: dict[str, Any], crossing_id: str, *, landing_revision: str
) -> dict[str, Any]:
    record = next(
        (item for item in state["crossing_records"] if item["crossing_id"] == crossing_id),
        None,
    )
    if record is None or record["status"] != "ADMITTED":
        raise EnvironmentRefused("CROSSING_NOT_ADMITTED")
    if landing_revision != record["revision"]:
        record["status"] = "REFUSED"
        record["receipt"] = _receipt(
            state, record, "REFUSED", "CANDIDATE_IDENTITY_CHANGED"
        )
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
    state["deployments"].append(deployment)
    record["status"] = "LANDED"
    record["deployment_id"] = deployment["deployment_id"]
    record["receipt"] = _receipt(state, record, "LANDED", None)
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


@dataclass
class StateStore:
    """Small local JSON store with process-level serialized writes."""

    path: Path

    @property
    def lock_path(self) -> Path:
        return self.path.with_suffix(self.path.suffix + ".lock")

    def read(self) -> dict[str, Any]:
        return load_json(self.path)

    def write(self, state: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_fd: int | None = None
        try:
            lock_fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(lock_fd, str(os.getpid()).encode())
        except FileExistsError as error:
            raise EnvironmentRefused("STATE_WRITE_BUSY") from error
        try:
            fd, temp_name = tempfile.mkstemp(prefix=self.path.name + ".", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, indent=2, sort_keys=True)
                handle.write("\n")
            os.replace(temp_name, self.path)
        finally:
            if lock_fd is not None:
                os.close(lock_fd)
            self.lock_path.unlink(missing_ok=True)
