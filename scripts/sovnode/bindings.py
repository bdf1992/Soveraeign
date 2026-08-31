"""Human and Model renderings of one canonical Node Interface operation record."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

from sovnode.affordances import INVOKABLE
from sovnode.affordances import binding_admission
from sovnode.affordances import defects as affordance_defects

HUMAN = "HUMAN"
MODEL = "MODEL"
BINDING_IDS = {
    HUMAN: "urn:soveraeign:binding:node-interface:human-cli-v1",
    MODEL: "urn:soveraeign:binding:node-interface:model-json-v1",
}


class BindingRefusal(RuntimeError):
    """The interface refuses to offer an action its sources do not expose."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def resolve(document: dict[str, Any], operation_id: str) -> dict[str, Any]:
    """Resolve one operation and verify its record digest before rendering it."""
    matches = [item for item in document.get("operations", [])
               if item.get("operation_id") == operation_id]
    if len(matches) != 1:
        raise BindingRefusal("OPERATION_UNKNOWN", operation_id)
    record = matches[0]
    material = dict(record)
    recorded = material.pop("record_digest", None)
    actual = sha256(_canonical(material).encode("utf-8")).hexdigest()
    if recorded != actual:
        raise BindingRefusal("INTERFACE_RECORD_DRIFT", operation_id)
    defects = affordance_defects(record)
    if defects:
        raise BindingRefusal("ROUTE_AFFORDANCE_DRIFT", "; ".join(defects))
    return record


def render_model(record: dict[str, Any]) -> str:
    """Typed Model projection with actor-kind admission kept separate from its route."""
    projected = dict(record)
    projected["binding_admission"] = binding_admission(record, MODEL)
    return json.dumps(projected)


def render_human(record: dict[str, Any]) -> str:
    """Compact operator text exposing the same identity, authority, and provenance."""
    facts = "  ".join(f"{name}={'yes' if value else 'no'}"
                      for name, value in record["facts"].items())
    sources = "\n".join(
        f"  {source['digest'][:12]}  {source['address']}" for source in record["sources"])
    choices = ", ".join(record["legal_choices"]) or "none"
    admission = binding_admission(record, HUMAN)
    return (
        f"{record['operation_id']}  [{record['record_digest'][:12]}]\n"
        f"{record['logical_endpoint']}\n"
        f"{facts}\n"
        f"authority  {record['required_authority']}\n"
        f"effect     {record['effect_class']}\n"
        f"actors     {', '.join(record['actor_kinds'])}\n"
        f"route      {record['route_affordance']['kind']} "
        f"({record['route_affordance']['reason_code']})\n"
        f"binding    HUMAN {'admitted' if admission['admitted'] else 'not admitted'} "
        f"({admission['reason_code']})\n"
        f"transition {record['kernel_transition'] or 'unmapped'}\n"
        f"choices    {choices}\n"
        f"sources\n{sources}"
    )


def invocation_request(document: dict[str, Any], operation_id: str, binding_kind: str,
                       actor: str, scope: str, arguments: dict[str, Any], *,
                       session_id: str, session_binding_id: str,
                       principal_id: str | None) -> dict[str, Any]:
    """Build one Gateway envelope; rendering never supplies a route or a grant.

    ``interface_binding_id`` names this Human/Model rendering. ``session_binding_id``
    names the host continuity binding pinned when the session opened. Keeping both
    prevents two different layers from collapsing into one overloaded binding id.
    """
    if binding_kind not in BINDING_IDS:
        raise BindingRefusal("BINDING_UNKNOWN", binding_kind)
    record = resolve(document, operation_id)
    if binding_kind not in record["actor_kinds"]:
        raise BindingRefusal("ACTOR_KIND_NOT_ADMITTED", operation_id)
    if record["route_affordance"]["kind"] not in INVOKABLE:
        raise BindingRefusal("OPERATION_NOT_REACHABLE", operation_id)
    routes = [route for route in record["reachability"] if route["policy_active"]]
    if len(routes) != 1:
        raise BindingRefusal("ROUTE_AMBIGUOUS", operation_id)
    if not session_id or not session_binding_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    if principal_id is not None and not principal_id:
        raise BindingRefusal("SESSION_IDENTITY_REQUIRED", operation_id)
    if ("session_id" in arguments and arguments["session_id"] != session_id):
        raise BindingRefusal("SESSION_ATTRIBUTION_CONFLICT", operation_id)
    return {
        "actor": actor,
        "actor_kind": binding_kind,
        "logical_endpoint": record["logical_endpoint"],
        "transport": routes[0]["transport"],
        "scope": scope,
        "arguments": dict(arguments),
        "session_id": session_id,
        "session_binding_id": session_binding_id,
        "principal_id": principal_id,
        "interface_binding_id": BINDING_IDS[binding_kind],
        "interface_operation_digest": record["record_digest"],
    }


__all__ = [
    "BINDING_IDS", "BindingRefusal", "HUMAN", "MODEL", "invocation_request",
    "render_human", "render_model", "resolve",
]
