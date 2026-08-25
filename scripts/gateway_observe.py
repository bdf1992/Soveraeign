"""Independent inspection of one durable Gateway vertical.

This module deliberately imports no service or Gateway implementation. It reads
the caller's return, the Record journal, the Asset ledger, authored declarations,
and the addressed payload bytes directly with the standard library.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any


GENESIS = "0" * 64
EXPECTED_KINDS = (
    "gateway-request",
    "gateway-capability-resolution",
    "gateway-authority-check",
    "gateway-routing-record",
    "gateway-returned-receipt",
)


def canonical(value: object) -> str:
    """Encode a value exactly as the Record Service's public contract declares."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _input_state_digest(repository: Path) -> tuple[str, str]:
    table = json.loads((repository / "contracts" / "capability-offices.json").read_text("utf-8"))
    manifests: dict[str, dict[str, Any]] = {}
    for path in sorted((repository / "services").glob("*/contracts/service.json")):
        manifest = json.loads(path.read_text("utf-8"))
        manifests[manifest["service_id"]] = manifest
    material = canonical({"manifests": manifests, "table": table})
    computed = sha256(material.encode("utf-8")).hexdigest()
    projected = json.loads(
        (repository / "contracts" / "fixtures" / "capability-map.reference.json")
        .read_text("utf-8")
    ).get("input_state_digest", "")
    return computed, projected


def _journal(state: Path) -> tuple[list[dict[str, Any]], list[str]]:
    database = state / "record" / "record-service.sqlite3"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = [dict(row) for row in connection.execute("SELECT * FROM journal ORDER BY seq")]
    finally:
        connection.close()
    defects: list[str] = []
    previous = GENESIS
    for row in rows:
        payload = json.loads(row["payload_json"])
        material = "|".join((previous, row["kind"], row["subject"], row["actor"],
                             canonical(payload)))
        expected = sha256(material.encode("utf-8")).hexdigest()
        if row["prev_digest"] != previous or row["entry_digest"] != expected:
            defects.append("JOURNAL_CHAIN_INVALID")
        previous = row["entry_digest"]
        row["payload"] = payload
    return rows, defects


def _asset_rows(state: Path, table: str) -> list[dict[str, Any]]:
    database = state / "asset" / "asset-service.sqlite3"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in connection.execute(f"SELECT * FROM {table}")]
    finally:
        connection.close()


def _gateway_events(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests = [row for row in rows if row["kind"] == "EVENT"
                and row["payload"].get("record_kind") == "gateway-request"]
    if len(requests) != 1:
        return []
    request_id = requests[0]["payload"].get("request_id")
    return [row for row in rows if row["kind"] == "EVENT"
            and row["payload"].get("request_id") == request_id]


def semantic_signature(repository: Path, state: Path,
                       caller_output: dict[str, Any]) -> dict[str, Any]:
    """Return only parity-invariant facts, excluding actor and generated identities."""
    rows, _ = _journal(state)
    events = _gateway_events(rows)
    by_kind = {row["payload"].get("record_kind"): row["payload"] for row in events}
    receipt = caller_output.get("returned_receipt", {})
    computed, projected = _input_state_digest(repository)
    return {
        "operation": by_kind.get("gateway-capability-resolution", {}).get("capability_id"),
        "transport": by_kind.get("gateway-routing-record", {}).get("transport"),
        "route": by_kind.get("gateway-routing-record", {}).get("route_address"),
        "authority": by_kind.get("gateway-authority-check", {}).get("required_authority"),
        "effect": by_kind.get("gateway-routing-record", {}).get("effect_class"),
        "terminal_event": receipt.get("event"),
        "terminal_outcome": receipt.get("outcome"),
        "input_state_digest": computed,
        "projected_input_state_digest": projected,
    }


def crossing_defects(repository: Path, state: Path, caller_output: dict[str, Any],
                     actor: str, actor_kind: str) -> list[str]:
    """Reconstruct the crossing without trusting Gateway or service read methods."""
    defects: list[str] = []
    try:
        rows, chain_defects = _journal(state)
        defects.extend(chain_defects)
        events = _gateway_events(rows)
        if [row["payload"].get("record_kind") for row in events] != list(EXPECTED_KINDS):
            return defects + ["CROSSING_SEQUENCE_INVALID"]
        by_kind = {row["payload"]["record_kind"]: row for row in events}
        request, resolution, authority, routing, returned = (
            by_kind[name] for name in EXPECTED_KINDS
        )
        computed, projected = _input_state_digest(repository)
        if computed != projected or resolution["payload"].get("capability_map_digest") != computed:
            defects.append("SOURCE_INPUT_STALE")
        if (request["actor"] != actor
                or request["payload"].get("actor_kind") != actor_kind
                or request["subject"] != "sov://asset/ingest-asset"):
            defects.append("REQUEST_ATTRIBUTION_INVALID")
        if (resolution["payload"].get("capability_id") != "asset.ingest-asset"
                or resolution["payload"].get("route_address") != "asset:in-process"):
            defects.append("RESOLUTION_INVALID")
        grant = authority["payload"].get("authority_grant_id")
        if (authority["payload"].get("decision") != "ALLOWED"
                or authority["payload"].get("required_authority") != "ingest:asset"
                or authority["payload"].get("resolution_entry_id") != resolution["entry_id"]
                or not grant):
            defects.append("AUTHORITY_EVIDENCE_INVALID")
        if (routing["payload"].get("request_entry_id") != request["entry_id"]
                or routing["payload"].get("resolution_entry_id") != resolution["entry_id"]
                or routing["payload"].get("authority_entry_id") != authority["entry_id"]
                or routing["payload"].get("authority_grant_id") != grant
                or routing["payload"].get("transport") != "IN_PROCESS"
                or routing["payload"].get("effect_class") != "RECORD_LOCAL"):
            defects.append("ROUTING_EVIDENCE_INVALID")
        terminal = caller_output.get("returned_receipt")
        receipts = _asset_rows(state, "receipts")
        if not isinstance(terminal, dict) or terminal not in receipts or len(receipts) != 1:
            defects.append("TERMINAL_RECEIPT_MISMATCH")
            terminal = terminal if isinstance(terminal, dict) else {}
        if (terminal.get("actor") != actor or terminal.get("event") != "asset.ingest"
                or terminal.get("outcome") != "COMMITTED"):
            defects.append("TERMINAL_ATTRIBUTION_INVALID")
        if (returned["payload"].get("routing_entry_id") != routing["entry_id"]
                or returned["payload"].get("terminal_receipt_id") != terminal.get("id")
                or returned["payload"].get("terminal_outcome") != "COMMITTED"):
            defects.append("RETURN_EVIDENCE_INVALID")
        if any(row["kind"] == "RECEIPT"
               and row["payload"].get("event") == "gateway.return-receipt" for row in rows):
            defects.append("GATEWAY_COUNTERFEIT_SETTLEMENT")
        assets = _asset_rows(state, "assets")
        versions, sources = _asset_rows(state, "versions"), _asset_rows(state, "sources")
        payload = json.loads(terminal.get("payload_json", "{}"))
        if (len(assets) != 1 or len(versions) != 1 or len(sources) != 1
                or terminal.get("subject_type") != "asset"
                or terminal.get("subject_id") != assets[0].get("id")
                or versions[0].get("asset_id") != assets[0].get("id")
                or payload.get("version_id") != versions[0].get("id")
                or payload.get("source_id") != sources[0].get("id")
                or versions[0].get("digest") != payload.get("digest")
                or sources[0].get("digest") != payload.get("digest")):
            defects.append("ASSET_STATE_INVALID")
        elif (sha256(Path(versions[0]["blob_path"]).read_bytes()).hexdigest()
              != payload.get("digest")):
            defects.append("ASSET_PAYLOAD_INVALID")
    except (KeyError, OSError, ValueError, sqlite3.Error, TypeError):
        defects.append("OBSERVATION_UNREADABLE")
    return list(dict.fromkeys(defects))
