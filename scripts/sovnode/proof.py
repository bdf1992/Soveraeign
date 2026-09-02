"""Drive the first Human/Model read and consequential action interface proof."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import json

from sovnode.bindings import (
    BINDING_IDS, HUMAN, MODEL, invocation_request, render_human, render_model, resolve,
)
from sovnode.composition import LocalActionPath
from sovnode.interface_inputs import rebuild


class _ProofHostAdapter:
    """Deterministic Host Port given for parity; not an observation of the test host."""

    adapter_id = "urn:soveraeign:adapter:node-interface-proof-host:v1"

    def read_health(self) -> dict[str, Any]:
        return {
            "schema_version": "soveraeign-host-health/v1",
            "adapter_id": self.adapter_id,
            "captured_at": "2026-08-25T12:00:00+00:00",
            "boundary": "PROCESS_EXECUTION_HOST",
            "platform": {"system": "ProofOS", "release": "1", "machine": "proof64"},
            "processor": {"logical_count": 2, "load_average": [0.0, 0.0, 0.0]},
            "memory": {"total_bytes": 4096, "available_bytes": 2048},
            "uptime_seconds": 60.0,
            "boot_id": "proof-boot-1",
            "limitations": ["deterministic_fixture_not_live_observation"],
        }


def _reason(receipt: dict[str, Any]) -> str | None:
    payload = receipt.get("payload")
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, dict):
            return detail.get("reason_code")
    return None


def _signatures(results: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Per-binding-kind result fields, minus the ones that differ by construction."""
    excluded = ("interface_binding_id", "terminal_receipt_id")
    return {kind: {name: value for name, value in result.items() if name not in excluded}
            for kind, result in results.items()}


def _open_session(node: LocalActionPath, actor: str, actor_kind: str) -> dict[str, Any]:
    issuer = "interface-proof-given"
    node.console.grant(actor, "open:session", actor, granted_by=issuer)
    host_binding = f"urn:soveraeign:binding:proof-host:{actor_kind.lower()}"
    return node.console.open_session(
        actor, actor_kind, host_binding, f"principal:{actor}")


def _request(document: dict[str, Any], operation_id: str, binding_kind: str,
             actor: str, scope: str, arguments: dict[str, Any],
             session: dict[str, Any]) -> dict[str, Any]:
    return invocation_request(
        document, operation_id, binding_kind, actor, scope, arguments,
        session_id=session["session_id"],
        session_binding_id=session["binding_id"],
        principal_id=session["principal_id"])


def _attribution_was_recorded(node: LocalActionPath, request: dict[str, Any]) -> bool:
    rows = [entry["payload"] for entry in node.record.entries()
            if entry["kind"] == "EVENT"
            and entry["payload"].get("record_kind") == "gateway-session-attribution"]
    if not rows:
        return False
    row = rows[-1]
    return (row.get("decision") == "ALLOWED"
            and all(row.get(field) == request.get(field) for field in (
                "session_id", "session_binding_id", "principal_id",
                "interface_binding_id", "interface_operation_digest")))


def _last_grant_id(node: LocalActionPath) -> str | None:
    rows = [entry["payload"] for entry in node.record.entries()
            if entry["kind"] == "EVENT"
            and entry["payload"].get("record_kind") == "gateway-routing-record"]
    return rows[-1].get("authority_grant_id") if rows else None


def _mismatch_attempt(node: LocalActionPath, document: dict[str, Any], operation: dict[str, Any],
                      source: Path, actor: str, scope: str, session: dict[str, Any], *,
                      principal_override: str | None = None, label: str) -> dict[str, Any]:
    request = _request(document, operation["operation_id"], HUMAN, actor, scope,
                       {"path": str(source), "label": label}, session)
    if principal_override is not None:
        request["principal_id"] = principal_override
    returned = node.dispatch(request)
    return {
        "session_attribution_recorded": _attribution_was_recorded(node, request),
        "outcome": returned["payload"]["outcome"],
        "reason_code": _reason(returned),
        "receipt_id": returned["entry_id"],
    }


def run() -> dict[str, Any]:
    """Return machine-checkable evidence; the fixture grants are givens, not UI output."""
    document, defects = rebuild()
    if defects:
        raise RuntimeError("Node Interface refused: " + "; ".join(defects))
    operation = resolve(document, "asset.ingest-asset")
    registry_operation = resolve(document, "registry.resolve")
    host_operation = resolve(document, "host.read-health")
    human_read, model_read = render_human(operation), render_model(operation)
    payload = b"human and model cross the same node interface\n"
    action_results: dict[str, dict[str, Any]] = {}
    registry_results: dict[str, dict[str, Any]] = {}
    host_results: dict[str, dict[str, Any]] = {}
    identity_snapshot: dict[str, Any] = {}

    with TemporaryDirectory() as work:
        root = Path(work)
        source = root / "proof-input.txt"
        source.write_bytes(payload)
        for binding_kind in (HUMAN, MODEL):
            actor = f"interface-{binding_kind.lower()}"
            scope = f"asset:new:{binding_kind.lower()}"
            with LocalActionPath(root / binding_kind.lower()) as node:
                session = _open_session(node, actor, binding_kind)
                node.console.grant(actor, operation["required_authority"], scope,
                                   granted_by="interface-proof-given")
                request = _request(
                    document, operation["operation_id"], binding_kind, actor, scope,
                    {"path": str(source), "label": "Interface proof"}, session)
                returned = node.dispatch(request)
                durable = node.asset.receipts()[-1]
                detail = json.loads(returned["payload_json"])
                action_results[binding_kind] = {
                    "interface_binding_id": request["interface_binding_id"],
                    "session_attribution_recorded": _attribution_was_recorded(node, request),
                    "operation_digest": request["interface_operation_digest"],
                    "required_authority": operation["required_authority"],
                    "terminal_receipt_id": returned["id"],
                    "terminal_outcome": returned["outcome"],
                    "terminal_event": returned["event"],
                    "payload_digest": detail["digest"],
                    "service_receipt_unchanged": returned == durable,
                }
                if binding_kind == HUMAN:
                    identity_snapshot = {
                        "principal_id": session["principal_id"],
                        "session_id": session["session_id"],
                        "grant_id": _last_grant_id(node),
                        "interface_binding_id": request["interface_binding_id"],
                    }

            with LocalActionPath(root / f"registry-{binding_kind.lower()}") as node:
                session = _open_session(node, actor, binding_kind)
                node.console.grant(actor, registry_operation["required_authority"],
                                   "registry:any", granted_by="interface-proof-given")
                request = _request(
                    document, registry_operation["operation_id"], binding_kind,
                    actor, "registry:any", {"name": "sov://asset/ingest-asset"}, session)
                returned = node.dispatch(request)
                detail = returned["payload"]["detail"]
                resolution = detail["resolution"]
                registry_results[binding_kind] = {
                    "interface_binding_id": request["interface_binding_id"],
                    "session_attribution_recorded": _attribution_was_recorded(node, request),
                    "operation_digest": request["interface_operation_digest"],
                    "required_authority": registry_operation["required_authority"],
                    "terminal_receipt_id": returned["entry_id"],
                    "terminal_outcome": returned["payload"]["outcome"],
                    "terminal_event": returned["payload"]["event"],
                    "resolved_capability": resolution["capability_id"],
                    "resolved_record_digest": resolution["record_digest"],
                    "source_digests": resolution["sources"],
                    "standing_effect": resolution["standing_effect"],
                    "service_receipt_unchanged": (
                        returned == node.record.entry(returned["entry_id"])),
                }

            with LocalActionPath(
                    root / f"host-{binding_kind.lower()}",
                    host_adapter=_ProofHostAdapter()) as node:
                session = _open_session(node, actor, binding_kind)
                node.console.grant(actor, host_operation["required_authority"],
                                   "host:local", granted_by="interface-proof-given")
                request = _request(
                    document, host_operation["operation_id"], binding_kind,
                    actor, "host:local", {}, session)
                returned = node.dispatch(request)
                detail = returned["payload"]["detail"]
                snapshot = detail["snapshot"]
                host_results[binding_kind] = {
                    "interface_binding_id": request["interface_binding_id"],
                    "session_attribution_recorded": _attribution_was_recorded(node, request),
                    "operation_digest": request["interface_operation_digest"],
                    "required_authority": host_operation["required_authority"],
                    "terminal_receipt_id": returned["entry_id"],
                    "terminal_outcome": returned["payload"]["outcome"],
                    "terminal_event": returned["payload"]["event"],
                    "boundary": snapshot["boundary"],
                    "adapter_id": snapshot["adapter_id"],
                    "snapshot_schema": snapshot["schema_version"],
                    "standing_effect": detail["standing_effect"],
                    "service_receipt_unchanged": (
                        returned == node.record.entry(returned["entry_id"])),
                }

        with LocalActionPath(root / "refused") as node:
            session = _open_session(node, "interface-refused", HUMAN)
            request = _request(
                document, operation["operation_id"], HUMAN, "interface-refused",
                "asset:new", {"path": str(source), "label": "Refused proof"}, session)
            refusal = node.dispatch(request)
            refusal_attribution = _attribution_was_recorded(node, request)

        with LocalActionPath(root / "inactive") as node:
            actor = "interface-human"
            session = _open_session(node, actor, HUMAN)
            inactive_operation = resolve(document, "console.resolve-judgement")
            inactive_request = {
                "actor": actor, "actor_kind": HUMAN,
                "session_id": session["session_id"],
                "session_binding_id": session["binding_id"],
                "principal_id": session["principal_id"],
                "interface_binding_id": BINDING_IDS[HUMAN],
                "interface_operation_digest": inactive_operation["record_digest"],
                "logical_endpoint": "sov://console/resolve-judgement",
                "transport": "IN_PROCESS", "scope": "judgement:any", "arguments": {},
            }
            inactive = node.dispatch(inactive_request)
            inactive_attribution = _attribution_was_recorded(node, inactive_request)

        with LocalActionPath(root / "mismatched") as node:
            actor_a, actor_b = "interface-mismatch-a", "interface-mismatch-b"
            session_a = _open_session(node, actor_a, HUMAN)
            session_b = _open_session(node, actor_b, HUMAN)
            scope_a, scope_b = "asset:new:mismatch-a", "asset:new:mismatch-b"
            node.console.grant(actor_a, operation["required_authority"], scope_a,
                               granted_by="interface-proof-given")
            node.console.grant(actor_b, operation["required_authority"], scope_b,
                               granted_by="interface-proof-given")
            # Neither attempt may borrow authority from the neighbouring, valid session.
            mismatch = {
                "cross_principal": _mismatch_attempt(
                    node, document, operation, source, actor_a, scope_a, session_a,
                    principal_override=session_b["principal_id"],
                    label="Cross-principal mismatch"),
                "cross_session_scope": _mismatch_attempt(
                    node, document, operation, source, actor_a, scope_b, session_a,
                    label="Cross-session scope borrow"),
            }
        cross_principal_session_mismatch = (
            "REFUSED" if all(row["outcome"] == "REFUSED" for row in mismatch.values())
            else "COMMITTED")

    semantic_signatures = _signatures(action_results)
    registry_signatures = _signatures(registry_results)
    host_signatures = _signatures(host_results)
    return {
        "proof_schema": "soveraeign-node-interface-proof/v1",
        "standing": "BUILT_EVIDENCE_SETTLES_NOTHING",
        "identities": identity_snapshot,
        "mismatch": mismatch,
        "cross_principal_session_mismatch": cross_principal_session_mismatch,
        "read": {
            "operation_id": operation["operation_id"],
            "record_digest": operation["record_digest"],
            "human_contains_digest": operation["record_digest"][:12] in human_read,
            "model_record_digest": json.loads(model_read)["record_digest"],
            "required_authority": operation["required_authority"],
        },
        "actions": action_results,
        "same_action_semantics": semantic_signatures[HUMAN] == semantic_signatures[MODEL],
        "registry_reads": registry_results,
        "same_registry_semantics": registry_signatures[HUMAN] == registry_signatures[MODEL],
        "host_reads": host_results,
        "same_host_semantics": host_signatures[HUMAN] == host_signatures[MODEL],
        "refusal": {
            "session_attribution_recorded": refusal_attribution,
            "outcome": refusal["payload"]["outcome"],
            "reason_code": _reason(refusal),
            "receipt_id": refusal["entry_id"],
        },
        "inactive_operation": {
            "session_attribution_recorded": inactive_attribution,
            "operation_id": "console.resolve-judgement",
            "outcome": inactive["payload"]["outcome"],
            "reason_code": _reason(inactive),
            "interface_reachable": resolve(
                document, "console.resolve-judgement")["facts"]["reachable"],
        },
    }


__all__ = ["run"]
