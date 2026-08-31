"""Pure helpers for the declared Gateway surface and terminal receipt shape."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Callable
import json

AuthorityCheck = Callable[[str, str, str], str]
AttributionCheck = Callable[[str, str, str, str, str | None], None]
ServiceRoute = Callable[[str, dict[str, Any], str], dict[str, Any]]

RECORD_LOCAL = "RECORD_LOCAL"
IN_PROCESS = "IN_PROCESS"
MCP = "MCP"
ACTIVE = "ACTIVE"
DECLARED = "DECLARED_NOT_ACTIVATED"
REFUSED = "REFUSED_UNCONFIGURED"
BUILT_STANDINGS = ("BUILT", "WITNESSED", "RATIFIED")
TERMINAL_OUTCOMES = ("COMMITTED", "REFUSED", "COUNTERED", "FAILED", "UNRESOLVED")
ATTRIBUTION_ARGUMENTS = frozenset({
    "actor", "actor_id", "actor_kind", "principal_id", "session_id",
    "session_binding_id", "interface_binding_id", "interface_operation_digest",
})


class GatewayRefusal(RuntimeError):
    """A governed refusal. Dispatch returns a durable REFUSED receipt."""

    def __init__(self, code: str, message: str, *, stage: str,
                 diagnostic_code: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.stage = stage
        self.diagnostic_code = diagnostic_code


class GatewayFault(RuntimeError):
    """An operational/configuration failure, distinct from lack of authority."""

    def __init__(self, code: str, message: str, *, event: str, stage: str,
                 error_type: str | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.event = event
        self.stage = stage
        self.error_type = error_type


def expected_endpoint(service_id: str, capability_id: str, standing: str,
                      transport: str, table: dict[str, Any]) -> dict[str, Any]:
    """Re-read policy inputs for endpoint fields carried by the projection."""
    endpoint: dict[str, Any] = {"transport": transport}
    built = standing in BUILT_STANDINGS
    refused = set(table.get("external_transports_refused_in_phase", []))
    cli_command = (table.get("cli_commands") or {}).get(capability_id)
    mcp_tool = (table.get("mcp_tools") or {}).get(capability_id)
    if transport in refused:
        endpoint["activation"] = REFUSED
        endpoint["refusal_code"] = "UNCONFIGURED"
    elif transport == IN_PROCESS and built:
        endpoint["activation"] = ACTIVE
        endpoint["address"] = f"{service_id}:in-process"
    elif transport == "CLI" and built and cli_command:
        endpoint["activation"] = ACTIVE
        endpoint["address"] = cli_command
    elif transport == MCP and built and mcp_tool:
        # Same rule as CLI, for the model-facing transport. Without this branch the
        # Gateway re-derives DECLARED_NOT_ACTIVATED for every MCP endpoint and calls
        # the map's ACTIVE rows drift, faulting CAPABILITY_MAP_INVALID on a correct
        # map. scripts/sovkernel/capability_map.py holds the same rule; the two
        # derive the projection independently and must stay in step.
        endpoint["activation"] = ACTIVE
        endpoint["address"] = mcp_tool
    else:
        endpoint["activation"] = DECLARED
    return endpoint


def receipt_outcome(receipt: dict[str, Any]) -> str | None:
    outcome = receipt.get("outcome")
    if isinstance(outcome, str):
        return outcome
    payload = receipt.get("payload")
    if isinstance(payload, dict) and isinstance(payload.get("outcome"), str):
        return payload["outcome"]
    return None


def receipt_actor(receipt: dict[str, Any]) -> str | None:
    actor = receipt.get("actor")
    if isinstance(actor, str) and actor:
        return actor
    actor = receipt.get("actor_id")
    if isinstance(actor, str) and actor:
        return actor
    return None


def receipt_id(receipt: dict[str, Any]) -> str | None:
    for name in ("receipt_id", "id", "entry_id"):
        value = receipt.get(name)
        if isinstance(value, str) and value:
            return value
    return None


def terminal_receipt(receipt: Any) -> bool:
    if not isinstance(receipt, dict):
        return False
    if receipt_outcome(receipt) not in TERMINAL_OUTCOMES or receipt_id(receipt) is None:
        return False
    if receipt.get("kind") == "RECEIPT":
        payload = receipt.get("payload")
        return (isinstance(payload, dict) and isinstance(payload.get("event"), str)
                and bool(payload["event"]) and receipt_actor(receipt) is not None)
    return (isinstance(receipt.get("event"), str) and bool(receipt["event"])
            and receipt_actor(receipt) is not None)


def request_actor_subject(request: Any) -> tuple[str, str]:
    mapping = request if isinstance(request, dict) else {}
    actor = mapping.get("actor")
    if not isinstance(actor, str) or not actor:
        actor = "unknown"
    subject = mapping.get("logical_endpoint")
    if not isinstance(subject, str) or not subject:
        subject = "gateway-request"
    return actor, subject


def input_state_digest(manifests: dict[str, dict[str, Any]], table: dict[str, Any]) -> str:
    material = json.dumps({"manifests": manifests, "table": table}, sort_keys=True,
                          separators=(",", ":"))
    return sha256(material.encode("utf-8")).hexdigest()


def load_surface(root: str | Path) -> tuple[
        dict[str, Any], dict[str, dict[str, Any]], dict[str, Any]]:
    """Load the checked projection and the exact authored inputs it projects."""
    root = Path(root)
    capability_map = json.loads(
        (root / "contracts" / "fixtures" / "capability-map.reference.json").read_text("utf-8"))
    capability_table = json.loads(
        (root / "contracts" / "capability-offices.json").read_text("utf-8"))
    manifests: dict[str, dict[str, Any]] = {}
    for path in sorted((root / "services").glob("*/contracts/service.json")):
        manifest = json.loads(path.read_text("utf-8"))
        manifests[manifest["service_id"]] = manifest
    return capability_map, manifests, capability_table
