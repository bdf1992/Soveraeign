"""Append-only journal of kernel entries with a verifiable chain.

This is the reference in-memory realization of the operational System of
Record's append rule (``AGENTS.md``, State and execution). Durable storage is
issue #7's obligation; it must keep this surface: ``append`` returns the sealed
entry, ``entries`` reads in order, nothing is updated or deleted, and ``audit``
exposes any entry that did not pass through ``append``.

Every entry digests its body together with the prior entry's digest. A service
that writes around the kernel either breaks the chain or leaves an event with no
receipt, and ``audit`` names it either way. The chain is not a security
boundary: it makes a bypass visible, which is what C1 and C7 require.
"""

from __future__ import annotations

from typing import Any

from .digests import digest_of

ENTRY_KINDS = (
    "GRANT", "RECORD", "EVENT", "RECEIPT", "ATTESTATION", "PLAN", "RUN", "REPORT",
    "OBSERVATION", "COUNTER",
)
TERMINAL_OUTCOMES = ("COMMITTED", "FAILED", "REFUSED", "COUNTERED", "UNRESOLVED")
GENESIS = "sha256:genesis"


def _seal(sequence: int, kind: str, body: dict[str, Any], prior: str) -> str:
    return digest_of({"sequence": sequence, "kind": kind, "body": body, "prior_digest": prior})


class Journal:
    """Ordered, append-preserving entries; the only write path is ``append``."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def append(self, kind: str, body: dict[str, Any]) -> dict[str, Any]:
        if kind not in ENTRY_KINDS:
            raise ValueError(f"unknown journal entry kind {kind!r}")
        prior = self._entries[-1]["entry_digest"] if self._entries else GENESIS
        sequence = len(self._entries)
        entry = {"sequence": sequence, "kind": kind, "body": body, "prior_digest": prior,
                 "entry_digest": _seal(sequence, kind, body, prior)}
        self._entries.append(entry)
        return entry

    def entries(self, kind: str | None = None) -> list[dict[str, Any]]:
        if kind is None:
            return list(self._entries)
        return [entry for entry in self._entries if entry["kind"] == kind]

    def bodies(self, kind: str) -> list[dict[str, Any]]:
        return [entry["body"] for entry in self._entries if entry["kind"] == kind]

    def __len__(self) -> int:
        return len(self._entries)

    def audit(self) -> list[str]:
        """Return every visible defect: broken chain, unreceipted event, orphan receipt."""
        defects = self._audit_chain()
        receipts = {body.get("receipt_id", "?"): body for body in self.bodies("RECEIPT")}
        events = {body.get("event_id", "?"): body for body in self.bodies("EVENT")}
        for event_id, event in events.items():
            receipt_id = event.get("receipt_id")
            if receipt_id is None:
                defects.append(f"event {event_id}: no receipt")
            elif receipt_id not in receipts or receipts[receipt_id].get("event_id") != event_id:
                defects.append(f"event {event_id}: receipt {receipt_id} is not on record")
        counts: dict[str, int] = {}
        for receipt_id, receipt in receipts.items():
            if receipt.get("event_id") not in events:
                defects.append(f"receipt {receipt_id}: event is not on record")
            if receipt.get("outcome") not in TERMINAL_OUTCOMES:
                defects.append(f"receipt {receipt_id}: outcome is not terminal")
            event_id = receipt.get("event_id", "?")
            counts[event_id] = counts.get(event_id, 0) + 1
        defects.extend(f"event {event_id}: {count} receipts, expected exactly one"
                       for event_id, count in counts.items() if count != 1)
        records = {body.get("record_id") for body in self.bodies("RECORD")}
        for counter in self.bodies("COUNTER"):
            if counter.get("target_record_id") not in records:
                defects.append(f"counter {counter.get('counter_record_id')}: "
                               "original record is not on record")
        return defects

    def _audit_chain(self) -> list[str]:
        defects: list[str] = []
        prior = GENESIS
        for position, entry in enumerate(self._entries):
            kind = entry.get("kind")
            if entry.get("sequence") != position or entry.get("prior_digest") != prior:
                defects.append(f"entry {position}: chain link does not match predecessor")
            elif entry.get("entry_digest") != _seal(position, kind, entry.get("body"), prior):
                defects.append(f"entry {position}: digest does not match body")
            if kind not in ENTRY_KINDS:
                defects.append(f"entry {position}: unknown kind {kind!r}")
            prior = entry.get("entry_digest", prior)
        return defects
