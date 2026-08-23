"""Typed authority evaluation at the transition boundary (SPEC.md AuthorityGrant).

A grant is checked for type, capability, scope, budget, time, and revocation at
the moment of the attempted transition, never earlier. The result is a list of
named predicate results so the receipt can say which gate refused. Budget spend
is derived from receipts already on record, not from a counter the grant keeps
(PROD-I-6: "Judgement use is reported from actual receipts").
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from .records import AuthorityGrant


def _parse(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def scope_covers(granted: str, requested: str) -> bool:
    """``*`` covers everything; ``a/b`` covers ``a/b`` and ``a/b/...``; nothing else matches."""
    if granted == "*" or granted == requested:
        return True
    return requested.startswith(granted.rstrip("/") + "/")


def evaluate(grant: AuthorityGrant | None, *, actor_id: str, authority_type: str,
             capability: str, scope: str, now: datetime, spent: int) -> list[dict[str, Any]]:
    """Return one ``{"predicate", "result"}`` entry per authority gate."""
    if grant is None:
        return [{"predicate": "grant_present", "result": False}]
    live = (grant.revoked_at is None
            and _parse(grant.valid_from) <= now <= _parse(grant.valid_until))
    return [
        {"predicate": "grant_present", "result": True},
        {"predicate": "actor_matches", "result": grant.actor_id == actor_id},
        {"predicate": "type_matches", "result": grant.authority_type == authority_type,
         "granted": grant.authority_type, "required": authority_type},
        {"predicate": "capability_matches", "result": grant.capability == capability},
        {"predicate": "scope_matches", "result": scope_covers(grant.scope, scope)},
        {"predicate": "grant_live", "result": live},
        {"predicate": "budget_available", "result": spent < grant.budget,
         "spent": spent, "budget": grant.budget},
    ]


def authorized(results: list[dict[str, Any]]) -> bool:
    return all(item["result"] for item in results)
