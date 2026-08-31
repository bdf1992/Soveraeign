"""Bind Environment promotion to the shared AuthorityGrant evaluator."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sovkernel import authority as kernel_authority
from sovkernel import jsonschema

from .errors import EnvironmentRefused
from .transitions import admit_crossing as _apply_admission

CAPABILITY = "environment.promote"


def crossing_record(state: dict[str, Any], crossing_id: str) -> dict[str, Any]:
    record = next(
        (item for item in state["crossing_records"] if item["crossing_id"] == crossing_id),
        None,
    )
    if record is None:
        raise EnvironmentRefused(f"CROSSING_UNKNOWN:{crossing_id}")
    return record


def environment_resource(state: dict[str, Any], record: dict[str, Any]) -> dict[str, str]:
    """The exact resource the owner-approved authority aperture scopes."""
    return {
        "pattern_digest": state["pattern_digest"],
        "trunk_instance": record["trunk_instance"],
        "source_instance": record["source_instance"],
        "target_instance": record["target_instance"],
        "revision": record["revision"],
        "artifact_digest": record["artifact_digest"],
    }


def build_request(
    state: dict[str, Any],
    crossing_id: str,
    *,
    actor_id: str,
    checks: dict[str, str] | None = None,
    observation: dict[str, Any] | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    record = crossing_record(state, crossing_id)
    return {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": actor_id,
        "capability": CAPABILITY,
        "effect_class": "RECORD_LOCAL",
        "at": at or datetime.now(timezone.utc).isoformat(),
        "resource": {"environment": environment_resource(state, record)},
        "evidence": {
            "checks": dict(checks or {}),
            "observation": observation,
        },
    }


def validate_grants(grants: list[dict[str, Any]], schema: dict[str, Any]) -> None:
    for grant in grants:
        failures = jsonschema.validate(grant, schema, schema)
        if failures:
            raise EnvironmentRefused(
                f"AUTHORITY_GRANT_INVALID:{grant.get('grant_id', '<unnamed>')}:"
                + "; ".join(failures)
            )


def authorize_crossing(
    state: dict[str, Any],
    crossing_id: str,
    *,
    actor_id: str,
    grants: list[dict[str, Any]],
    grant_schema: dict[str, Any],
    checks: dict[str, str] | None = None,
    observation: dict[str, Any] | None = None,
    at: str | None = None,
) -> dict[str, str]:
    """Return the covering grant identity/type, or refuse without mutating state."""
    if not grants:
        raise EnvironmentRefused("AUTHORITY_REFUSED:NO_ENVIRONMENT_GRANT_OFFERED")
    validate_grants(grants, grant_schema)
    request = build_request(
        state,
        crossing_id,
        actor_id=actor_id,
        checks=checks,
        observation=observation,
        at=at,
    )
    result = kernel_authority.evaluate(grants, request)
    if result["verdict"] != kernel_authority.PERMITTED:
        raise EnvironmentRefused(f"{result['code']}:{result['detail']}")
    covering = next(grant for grant in grants if grant["grant_id"] == result["grant_id"])
    return {
        "grant_id": covering["grant_id"],
        "authority_type": covering["authority_type"],
    }


def admit_crossing(
    state: dict[str, Any],
    pattern: dict[str, Any],
    crossing_id: str,
    *,
    current_integration_base: str,
    witness: str,
    grants: list[dict[str, Any]],
    grant_schema: dict[str, Any],
    checks: dict[str, str] | None = None,
    observation: dict[str, Any] | None = None,
    accepted: bool | None = None,
    at: str | None = None,
) -> dict[str, Any]:
    """Governed public admission: evaluate first, then apply the pure transition."""
    granted = authorize_crossing(
        state,
        crossing_id,
        actor_id=witness,
        grants=grants,
        grant_schema=grant_schema,
        checks=checks,
        observation=observation,
        at=at,
    )
    return _apply_admission(
        state,
        pattern,
        crossing_id,
        current_integration_base=current_integration_base,
        witness=witness,
        authority=granted["authority_type"],
        authority_grant_id=granted["grant_id"],
        accepted=accepted,
    )
