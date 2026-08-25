"""Human and Model renderings of one canonical Node Interface operation record."""

from __future__ import annotations

from hashlib import sha256
from typing import Any
import json

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
    return record


def render_model(record: dict[str, Any]) -> str:
    """Typed JSON for a model; the underlying record is unchanged."""
    return json.dumps(record, indent=2, sort_keys=True)


def render_human(record: dict[str, Any]) -> str:
    """Compact operator text exposing the same identity, authority, and provenance."""
    facts = "  ".join(f"{name}={'yes' if value else 'no'}"
                      for name, value in record["facts"].items())
    sources = "\n".join(
        f"  {source['digest'][:12]}  {source['address']}" for source in record["sources"])
    choices = ", ".join(record["legal_choices"]) or "none"
    return (
        f"{record['operation_id']}  [{record['record_digest'][:12]}]\n"
        f"{record['logical_endpoint']}\n"
        f"{facts}\n"
        f"authority  {record['required_authority']}\n"
        f"effect     {record['effect_class']}\n"
        f"actors     {', '.join(record['actor_kinds'])}\n"
        f"transition {record['kernel_transition'] or 'unmapped'}\n"
        f"choices    {choices}\n"
        f"sources\n{sources}"
    )


def invocation_request(document: dict[str, Any], operation_id: str, binding_kind: str,
                       actor: str, scope: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Build one Gateway envelope; rendering never supplies a route or a grant."""
    if binding_kind not in BINDING_IDS:
        raise BindingRefusal("BINDING_UNKNOWN", binding_kind)
    record = resolve(document, operation_id)
    if not record["facts"]["reachable"]:
        raise BindingRefusal("OPERATION_NOT_REACHABLE", operation_id)
    if binding_kind not in record["actor_kinds"]:
        raise BindingRefusal("ACTOR_KIND_NOT_ADMITTED", operation_id)
    routes = [route for route in record["reachability"] if route["policy_active"]]
    if len(routes) != 1:
        raise BindingRefusal("ROUTE_AMBIGUOUS", operation_id)
    return {
        "actor": actor,
        "actor_kind": binding_kind,
        "logical_endpoint": record["logical_endpoint"],
        "transport": routes[0]["transport"],
        "scope": scope,
        "arguments": dict(arguments),
        "binding_id": BINDING_IDS[binding_kind],
        "interface_operation_digest": record["record_digest"],
    }


__all__ = [
    "BINDING_IDS", "BindingRefusal", "HUMAN", "MODEL", "invocation_request",
    "render_human", "render_model", "resolve",
]
