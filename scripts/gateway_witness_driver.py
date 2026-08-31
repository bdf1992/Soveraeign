#!/usr/bin/env python3
"""Drive the exact Gateway vertical for an external observer process."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from soveraeign_asset_service import AssetService
from soveraeign_asset_service.routes import AssetRoutes
from soveraeign_console_service import ConsoleService
from soveraeign_console_service import authority as console_authority
from soveraeign_console_service import reads as console_reads
from soveraeign_console_service.refusals import (
    ActorAttributionMismatch, AuthorityRefused, SessionClosed, UnknownRecord,
)
from soveraeign_gateway_service import Gateway, load_surface
from soveraeign_record_service import RecordService


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = b"gateway witness payload\n"


def drive(state: Path, actor: str, actor_kind: str) -> dict[str, object]:
    """Cross one declared route and return only what its caller received."""
    state.mkdir(parents=True, exist_ok=False)
    source = state / "source.txt"
    source.write_bytes(PAYLOAD)
    record = RecordService(state / "record")
    console = ConsoleService(record, state / "console", "node:gateway-witness")
    asset = AssetService(state / "asset")
    try:
        scope = f"asset:new:{actor}"
        console.grant(actor, "open:session", actor, "Bdo")
        session = console.open_session(
            actor, actor_kind,
            f"urn:soveraeign:binding:gateway-witness:{actor_kind.lower()}")
        console.grant(actor, "ingest:asset", scope, "Bdo")
        capability_map, manifests, capability_table = load_surface(ROOT)
        interface = json.loads((ROOT / "contracts" / "fixtures" /
                                "node-interface.reference.json").read_text("utf-8"))
        operation = next(row for row in interface["operations"]
                         if row["operation_id"] == "asset.ingest-asset")

        def attribution(checked_actor: str, checked_kind: str, session_id: str,
                        session_binding_id: str, principal_id: str | None) -> None:
            try:
                held = console_reads.session(record.reconstruct(), session_id)
            except UnknownRecord:
                raise ActorAttributionMismatch("witness session is unknown") from None
            if (held.get("node_id") != console.node_id
                    or held.get("operator_id") != checked_actor
                    or held.get("actor_kind") != checked_kind
                    or held.get("binding_id") != session_binding_id
                    or held.get("principal_id") != principal_id):
                raise ActorAttributionMismatch("witness session attribution mismatch")
            if held.get("lifecycle") != "OPEN":
                raise SessionClosed(f"session {session_id} is CLOSED")

        gateway = Gateway(
            record,
            capability_map,
            manifests,
            capability_table,
            lambda checked_actor, capability, checked_scope: console_authority.check(
                record.reconstruct(), console.node_id, checked_actor, capability,
                checked_scope
            ),
            {"asset:in-process": AssetRoutes(asset).call},
            attribution=attribution,
            authority_denials=(AuthorityRefused,),
            attribution_denials=(ActorAttributionMismatch, SessionClosed),
        )
        returned = gateway.dispatch({
            "actor": actor,
            "actor_kind": actor_kind,
            "session_id": session["session_id"],
            "session_binding_id": session["binding_id"],
            "principal_id": session.get("principal_id"),
            "interface_binding_id": "urn:soveraeign:binding:gateway-witness-interface",
            "interface_operation_digest": operation["record_digest"],
            "logical_endpoint": "sov://asset/ingest-asset",
            "transport": "IN_PROCESS",
            "scope": scope,
            "arguments": {"path": str(source), "label": "Gateway Witness"},
        })
        return {"returned_receipt": returned}
    finally:
        asset.close()
        record.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--actor-kind", required=True, choices=("HUMAN", "MODEL"))
    args = parser.parse_args(argv)
    try:
        result = drive(args.state.resolve(), args.actor, args.actor_kind)
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"outcome": "FAILED", "error_type": type(error).__name__}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
