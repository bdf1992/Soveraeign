"""Drive the first Human/Model read and consequential action interface proof."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import json

from sovnode.bindings import HUMAN, MODEL, invocation_request, render_human, render_model, resolve
from sovnode.composition import LocalActionPath
from sovnode.interface_inputs import rebuild


def _reason(receipt: dict[str, Any]) -> str | None:
    payload = receipt.get("payload")
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, dict):
            return detail.get("reason_code")
    return None


def run() -> dict[str, Any]:
    """Return machine-checkable evidence; the fixture grants are givens, not UI output."""
    document, defects = rebuild()
    if defects:
        raise RuntimeError("Node Interface refused: " + "; ".join(defects))
    operation = resolve(document, "asset.ingest-asset")
    human_read, model_read = render_human(operation), render_model(operation)
    payload = b"human and model cross the same node interface\n"
    action_results: dict[str, dict[str, Any]] = {}

    with TemporaryDirectory() as work:
        root = Path(work)
        source = root / "proof-input.txt"
        source.write_bytes(payload)
        for binding_kind in (HUMAN, MODEL):
            actor = f"interface-{binding_kind.lower()}"
            scope = f"asset:new:{binding_kind.lower()}"
            with LocalActionPath(root / binding_kind.lower()) as node:
                node.console.grant(actor, operation["required_authority"], scope,
                                   granted_by="interface-proof-given")
                request = invocation_request(
                    document, operation["operation_id"], binding_kind, actor, scope,
                    {"path": str(source), "label": "Interface proof"})
                returned = node.dispatch(request)
                durable = node.asset.receipts()[-1]
                detail = json.loads(returned["payload_json"])
                action_results[binding_kind] = {
                    "binding_id": request["binding_id"],
                    "operation_digest": request["interface_operation_digest"],
                    "required_authority": operation["required_authority"],
                    "terminal_receipt_id": returned["id"],
                    "terminal_outcome": returned["outcome"],
                    "terminal_event": returned["event"],
                    "payload_digest": detail["digest"],
                    "service_receipt_unchanged": returned == durable,
                }

        with LocalActionPath(root / "refused") as node:
            request = invocation_request(
                document, operation["operation_id"], HUMAN, "interface-refused", "asset:new",
                {"path": str(source), "label": "Refused proof"})
            refusal = node.dispatch(request)

        with LocalActionPath(root / "inactive") as node:
            inactive = node.dispatch({
                "actor": "interface-human", "actor_kind": "HUMAN",
                "logical_endpoint": "sov://registry/resolve",
                "transport": "IN_PROCESS", "scope": "registry:any", "arguments": {},
            })

    semantic_signatures = {
        kind: {name: value for name, value in result.items()
               if name not in ("binding_id", "terminal_receipt_id")}
        for kind, result in action_results.items()
    }
    return {
        "proof_schema": "soveraeign-node-interface-proof/v1",
        "standing": "BUILT_EVIDENCE_SETTLES_NOTHING",
        "read": {
            "operation_id": operation["operation_id"],
            "record_digest": operation["record_digest"],
            "human_contains_digest": operation["record_digest"][:12] in human_read,
            "model_record_digest": json.loads(model_read)["record_digest"],
            "required_authority": operation["required_authority"],
        },
        "actions": action_results,
        "same_action_semantics": semantic_signatures[HUMAN] == semantic_signatures[MODEL],
        "refusal": {
            "outcome": refusal["payload"]["outcome"],
            "reason_code": _reason(refusal),
            "receipt_id": refusal["entry_id"],
        },
        "inactive_operation": {
            "operation_id": "registry.resolve",
            "outcome": inactive["payload"]["outcome"],
            "reason_code": _reason(inactive),
            "interface_reachable": resolve(document, "registry.resolve")["facts"]["reachable"],
        },
    }


__all__ = ["run"]
