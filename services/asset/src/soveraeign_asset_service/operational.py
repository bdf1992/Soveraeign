"""The Asset Service port into the append-preserving operational journal.

Asset owns its domain state. Record owns operational history. This module is the
small adapter between those ownership boundaries: it mirrors an already-durable
Asset terminal receipt into Record without making Record authoritative for Asset
rows and without treating the mirror as a grant.
"""

from __future__ import annotations

from typing import Any, Protocol
import json


SOURCE_ADDRESS = "asset-service"
RECORD_KIND = "asset-terminal-receipt"


class OperationalJournal(Protocol):
    """Only the Record behavior Asset needs; no dependency on Record implementation."""

    def entries(self) -> list[dict[str, Any]]: ...

    def append(self, kind: str, subject: str, actor: str, payload: dict[str, Any],
               source_address: str | None = None) -> dict[str, Any]: ...


def _existing(journal: OperationalJournal, receipt_id: str) -> dict[str, Any] | None:
    """A prior mirror of this exact local receipt, if one already reached Record."""
    for entry in journal.entries():
        if entry.get("kind") != "RECEIPT" or entry.get("source_address") != SOURCE_ADDRESS:
            continue
        detail = entry.get("payload", {}).get("detail", {})
        if detail.get("record_kind") == RECORD_KIND and detail.get("asset_receipt_id") == receipt_id:
            return entry
    return None


def mirror_receipt(journal: OperationalJournal, receipt: dict[str, Any]) -> str:
    """Mirror one committed Asset receipt idempotently and return its Record entry id."""
    existing = _existing(journal, receipt["id"])
    if existing is not None:
        return existing["entry_id"]
    detail = {
        "record_kind": RECORD_KIND,
        "source_service": "asset",
        "asset_receipt_id": receipt["id"],
        "subject_type": receipt["subject_type"],
        "local_payload": json.loads(receipt["payload_json"]),
        "local_created_at": receipt["created_at"],
    }
    entry = journal.append(
        "RECEIPT", f"asset:{receipt['subject_type']}:{receipt['subject_id']}",
        receipt["actor"],
        {"outcome": receipt["outcome"], "event": receipt["event"], "detail": detail},
        source_address=SOURCE_ADDRESS,
    )
    return entry["entry_id"]


__all__ = ["OperationalJournal", "mirror_receipt"]
