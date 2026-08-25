"""Derive UI affordances from Node Interface facts without granting authority."""

from __future__ import annotations

from typing import Any

ACTION = "ACTION"
READ = "READ"
INSPECT = "INSPECT"
HARNESS = "HARNESS"
NONE = "NONE"
INVOKABLE = frozenset({ACTION, READ})


def derive(record: dict[str, Any]) -> dict[str, str]:
    """Return presentation semantics from route and policy facts already in the record."""
    facts = record["facts"]
    routes = record.get("reachability", [])
    if facts["reachable"]:
        if record["crud"] == "READ":
            return {
                "kind": READ,
                "reason_code": "EXACT_READ_ROUTE_ACTIVE",
                "explanation": "An exact policy-active service route exposes this read.",
            }
        return {
            "kind": ACTION,
            "reason_code": "EXACT_ROUTE_ACTIVE",
            "explanation": "An exact policy-active service route exposes this operation.",
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


def defects(record: dict[str, Any]) -> list[str]:
    """Report an affordance that differs from the facts from which it must be derived."""
    expected = derive(record)
    actual = record.get("affordance")
    if actual != expected:
        return [
            f"AFFORDANCE_DRIFT: {record.get('operation_id', '<unknown>')} records "
            f"{actual!r}; derived value is {expected!r}"
        ]
    return []


__all__ = [
    "ACTION", "HARNESS", "INSPECT", "INVOKABLE", "NONE", "READ", "defects", "derive",
]
