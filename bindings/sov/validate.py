#!/usr/bin/env python3
"""Validate the portable Sov profile and one bounded context declaration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import sys


ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "bindings" / "sov" / "profile.json"
MINIMUM_CONTEXT = {"AGENTS.md", "SOV.md", "STATUS.yaml"}
EFFECTS = {"RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD"}
PROFILE_FIELDS = {
    "$schema",
    "schema_version",
    "profile_id",
    "display_name",
    "profile_kind",
    "profile_status",
    "entrypoint",
    "portable",
    "default_effect_class",
    "governing_sources",
    "minimum_context",
    "context_selection",
    "authority",
    "state",
    "agency",
    "session_declaration_schema",
    "activation_gates",
    "dynamic_context_gate",
    "fallback_policy",
}
SESSION_FIELDS = {
    "schema_version",
    "profile_id",
    "profile_revision",
    "artifact_revision",
    "actor_id",
    "host_id",
    "model_binding_id",
    "task",
    "requested_operation",
    "requested_effect_class",
    "live_grant_ids",
    "loaded_sources",
    "material_omissions",
    "expected_observation",
    "refusal_boundary",
    "authority_claimed_by_context",
    "private_durable_state",
    "fallback_requested",
}


class ContextRefused(ValueError):
    """A Sov context declaration failed a stable refusal boundary."""


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContextRefused(f"INVALID_JSON:{path.name}") from error
    if not isinstance(value, dict):
        raise ContextRefused(f"OBJECT_REQUIRED:{path.name}")
    return value


def validate_profile(profile: dict[str, Any]) -> None:
    """Refuse a profile that claims authority, state, settlement, or fallback."""
    if set(profile) != PROFILE_FIELDS:
        raise ContextRefused("PROFILE_FIELDS_INVALID")
    expected = {
        "schema_version": 1,
        "profile_id": "sov",
        "display_name": "Sov",
        "profile_kind": "MODEL_CONTEXT_PROFILE",
        "entrypoint": "SOV.md",
        "portable": True,
        "profile_status": "BUILT_SELF_TESTED_NOT_WITNESSED",
        "default_effect_class": None,
        "context_selection": (
            "OWNING_DOCUMENTS_PLUS_RELEVANT_CONTRACT_FIXTURE_SERVICE_DECISION_ISSUE"
        ),
        "session_declaration_schema": "bindings/sov/session.schema.json",
        "dynamic_context_gate": "issue:42",
        "fallback_policy": "NONE",
    }
    for field, value in expected.items():
        if profile.get(field) != value:
            raise ContextRefused(f"PROFILE_INVARIANT:{field}")
    authority = profile.get("authority")
    if not isinstance(authority, dict):
        raise ContextRefused("PROFILE_AUTHORITY_INVALID")
    if authority.get("granted_by_profile") is not False:
        raise ContextRefused("PROFILE_AUTHORITY_REFUSED")
    if authority.get("source") != "LIVE_TYPED_GRANT_AT_OPERATION_BOUNDARY":
        raise ContextRefused("PROFILE_AUTHORITY_SOURCE_INVALID")
    state = profile.get("state")
    if not isinstance(state, dict):
        raise ContextRefused("PROFILE_STATE_INVALID")
    if state.get("owns_authoritative_state") is not False:
        raise ContextRefused("PROFILE_STATE_OWNERSHIP_REFUSED")
    if state.get("allows_private_durable_state") is not False:
        raise ContextRefused("PRIVATE_STATE_REFUSED")
    agency = profile.get("agency")
    if not isinstance(agency, dict) or not isinstance(agency.get("may_not"), list):
        raise ContextRefused("PROFILE_AGENCY_INVALID")
    forbidden = set(agency["may_not"])
    required_refusals = {
        "INFER_AUTHORITY_FROM_CONTEXT",
        "RATIFY_JUDGEMENT",
        "SELF_WITNESS",
        "SELF_SETTLE",
        "KEEP_PRIVATE_STANDING",
        "SILENT_MODEL_FALLBACK",
    }
    if not required_refusals <= forbidden:
        raise ContextRefused("PROFILE_REFUSALS_INCOMPLETE")
    minimum_context = profile.get("minimum_context")
    if not isinstance(minimum_context, list) or not MINIMUM_CONTEXT <= set(minimum_context):
        raise ContextRefused("PROFILE_CONTEXT_INCOMPLETE")


def validate_session(session: dict[str, Any]) -> dict[str, Any]:
    """Validate context readiness without authorizing the requested operation."""
    if set(session) != SESSION_FIELDS:
        raise ContextRefused("SESSION_FIELDS_INVALID")
    required_strings = (
        "artifact_revision",
        "actor_id",
        "host_id",
        "model_binding_id",
        "task",
        "requested_operation",
        "expected_observation",
        "refusal_boundary",
    )
    if session.get("schema_version") != 1 or session.get("profile_revision") != 1:
        raise ContextRefused("SESSION_REVISION_UNSUPPORTED")
    if session.get("profile_id") != "sov":
        raise ContextRefused("SESSION_PROFILE_MISMATCH")
    for field in required_strings:
        if not isinstance(session.get(field), str) or not session[field].strip():
            raise ContextRefused(f"SESSION_FIELD_REQUIRED:{field}")
    if session.get("authority_claimed_by_context") is not False:
        raise ContextRefused("PROFILE_AUTHORITY_REFUSED")
    if session.get("private_durable_state") is not False:
        raise ContextRefused("PRIVATE_STATE_REFUSED")
    if session.get("fallback_requested") is not False:
        raise ContextRefused("SILENT_FALLBACK_REFUSED")
    for field in ("live_grant_ids", "loaded_sources", "material_omissions"):
        value = session.get(field)
        invalid_item = isinstance(value, list) and any(
            not isinstance(item, str) or not item for item in value
        )
        if not isinstance(value, list) or invalid_item:
            raise ContextRefused(f"SESSION_LIST_REQUIRED:{field}")
        if len(value) != len(set(value)):
            raise ContextRefused(f"SESSION_LIST_DUPLICATE:{field}")
    if not MINIMUM_CONTEXT <= set(session["loaded_sources"]):
        raise ContextRefused("MINIMUM_CONTEXT_MISSING")
    effect = session.get("requested_effect_class")
    if effect is not None and effect not in EFFECTS:
        raise ContextRefused("EFFECT_CLASS_INVALID")
    if effect is not None:
        raise ContextRefused("LIVE_GRANT_RESOLUTION_UNAVAILABLE")
    return {
        "schema": "soveraeign-sov-context-check/v1",
        "profile_id": "sov",
        "profile_revision": 1,
        "artifact_revision": session["artifact_revision"],
        "requested_operation": session["requested_operation"],
        "requested_effect_class": effect,
        "outcome": "CONTEXT_READY",
        "operation_authorized": False,
        "authority_source": "OPERATION_BOUNDARY_NOT_PROFILE",
        "material_omissions": session["material_omissions"],
    }


def check(path: Path) -> dict[str, Any]:
    """Load and validate the fixed profile plus one session declaration."""
    profile = _load_object(PROFILE_PATH)
    validate_profile(profile)
    return validate_session(_load_object(path))


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print(json.dumps({"outcome": "REFUSED", "reason_code": "DECLARATION_PATH_REQUIRED"}))
        return 2
    try:
        result = check(Path(arguments[0]))
    except ContextRefused as error:
        print(json.dumps({"outcome": "REFUSED", "reason_code": str(error)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
