"""Derive actor-neutral route facts and actor-kind binding admission."""

from __future__ import annotations

from typing import Any

ACTION = "ACTION"
READ = "READ"
INSPECT = "INSPECT"
HARNESS = "HARNESS"
NONE = "NONE"
INVOKABLE = frozenset({ACTION, READ})


def derive(record: dict[str, Any]) -> dict[str, str]:
    """Return actor-neutral semantics from route and policy facts in the record."""
    facts = record["facts"]
    routes = record.get("reachability", [])
    if facts["reachable"]:
        if record["crud"] == "READ":
            return {
                "kind": READ,
                "reason_code": "EXACT_READ_ROUTE_ACTIVE",
                "explanation": "An exact policy-active service route exists for this read.",
            }
        return {
            "kind": ACTION,
            "reason_code": "EXACT_ROUTE_ACTIVE",
            "explanation": "An exact policy-active service route exists for this operation.",
        }
    if facts["policy_active"]:
        reason = "ACTIVE_POLICY_HAS_NO_EXACT_ROUTE"
        explanation = "Policy is active, but this composition has no exact service-owned route."
    elif routes:
        reason = "EXACT_ROUTE_NOT_POLICY_ACTIVE"
        explanation = "An exact route is known, but policy does not activate it."
    else:
        reason = "NO_EXACT_ROUTE"
        explanation = "The operation is declared topology only; no exact route is bound."
    return {"kind": INSPECT, "reason_code": reason, "explanation": explanation}


def binding_admission(record: dict[str, Any], actor_kind: str) -> dict[str, Any]:
    """State actor-kind admission without claiming the actor holds live authority."""
    admitted = actor_kind in record.get("actor_kinds", [])
    if not admitted:
        return {
            "actor_kind": actor_kind,
            "admitted": False,
            "reason_code": "ACTOR_KIND_NOT_ADMITTED",
            "explanation": (
                f"{actor_kind} is not admitted by this operation's capability policy."
            ),
        }
    return {
        "actor_kind": actor_kind,
        "admitted": True,
        "reason_code": "ACTOR_KIND_ADMITTED",
        "explanation": (
            "The actor kind is admitted; live operator authority is not projected and is "
            "checked at dispatch."
        ),
    }


def defects(record: dict[str, Any]) -> list[str]:
    """Report a route affordance that differs from its source facts."""
    expected = derive(record)
    actual = record.get("route_affordance")
    if actual != expected:
        return [
            f"ROUTE_AFFORDANCE_DRIFT: {record.get('operation_id', '<unknown>')} records "
            f"{actual!r}; derived value is {expected!r}"
        ]
    return []


__all__ = [
    "ACTION", "HARNESS", "INSPECT", "INVOKABLE", "NONE", "READ", "binding_admission",
    "defects", "derive",
]
