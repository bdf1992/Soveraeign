"""Infer whether a candidate observer is independent of a run, from the run's record alone.

`decisions/0041-the-observation-service.md`, Ruling 2: nobody declares their own independence.
The walk looks for the five direct edges `CHARTER.md` names and `relation-inference.schema.json`
enforces. One edge found is `DIRECT`. None found over a record that answered every edge is
`INDEPENDENT`. A record that could not answer an edge is `UNDETERMINED`, which refuses: absence
of a recorded edge is not absence of a relation.

A found edge answers the question the inference asks, so a record that shows the candidate
executing the run reads `DIRECT` even when another edge could not be examined. Only a record
that found nothing and could not answer everything reads `UNDETERMINED`. That precedence is a
default taken here: it refuses in both cases, and it keeps the refusal's name honest.
"""

from __future__ import annotations

from typing import Any
import hashlib

from .errors import ObserverNotIndependent, RelationUndetermined, RunNotTerminal, Unreadable
from .record import RunRecord

EDGES = (
    "SAME_ACTOR",
    "HOLDS_RUN_LEASE",
    "GRANT_DESCENDS_FROM_RUN",
    "PRODUCED_THE_OUTPUT",
    "ONLY_EXECUTOR_REPORT",
)


class _Walk:
    """Accumulates findings, unanswerable edges, and the entries read to reach them."""

    def __init__(self) -> None:
        self.found: list[dict[str, str]] = []
        self.unanswerable: list[str] = []
        self.read: list[dict[str, Any]] = []

    def edge(self, name: str, entry: dict[str, Any]) -> None:
        self.found.append({"edge": name, "evidence_address": RunRecord.address_of(entry)})

    def cannot_answer(self, name: str) -> None:
        if name not in self.unanswerable:
            self.unanswerable.append(name)

    def cite(self, *entries: dict[str, Any]) -> None:
        for entry in entries:
            if entry not in self.read:
                self.read.append(entry)


def _walk_grants(record: RunRecord, candidate: str, run_grant: str, walk: _Walk) -> None:
    """Does any grant the candidate holds descend from the run's grant?"""
    grants = record.grants()
    held = [entry for entry in grants.values()
            if entry.get("payload", {}).get("holder_id") == candidate]
    if not held:
        walk.cannot_answer("GRANT_DESCENDS_FROM_RUN")
        return
    walk.cite(*held)
    for entry in held:
        seen: set[str] = set()
        current: dict[str, Any] | None = entry
        while current is not None:
            grant_id = str(current["subject"])
            if grant_id in seen:
                break
            seen.add(grant_id)
            if grant_id == run_grant:
                walk.edge("GRANT_DESCENDS_FROM_RUN", entry)
                return
            parent = current.get("payload", {}).get("parent_grant_id")
            if parent is None:
                break
            current = grants.get(str(parent))
            if current is None:
                walk.cannot_answer("GRANT_DESCENDS_FROM_RUN")
                return
            walk.cite(current)


def _walk_outputs(record: RunRecord, candidate: str, walk: _Walk) -> None:
    """Did the candidate produce an output, and is there anything but the report to read?"""
    report = record.report()
    if report is None:
        walk.cannot_answer("PRODUCED_THE_OUTPUT")
        walk.cannot_answer("ONLY_EXECUTOR_REPORT")
        return
    walk.cite(report)
    addresses = record.reported_addresses()
    outputs = record.outputs()
    present = [outputs[address] for address in addresses if address in outputs]
    walk.cite(*present)
    if len(present) != len(addresses):
        walk.cannot_answer("PRODUCED_THE_OUTPUT")
    elif any(entry.get("actor") == candidate for entry in present):
        walk.edge("PRODUCED_THE_OUTPUT", next(e for e in present if e.get("actor") == candidate))
    if not present:
        walk.edge("ONLY_EXECUTOR_REPORT", report)


def infer_relation(
    record: RunRecord,
    candidate_observer_id: str,
    candidate_observer_kind: str,
    inferred_at: str,
) -> dict[str, Any]:
    """Walk the run's record for a direct edge to the candidate. Raises on refusal.

    Returns a record shaped by `relation-inference.schema.json`. `DIRECT` and `INDEPENDENT`
    are returned; `UNDETERMINED` is returned as well, because the manifest promises the
    inference is recorded, and the caller refuses `RELATION_UNDETERMINED` on it.
    """
    if not record.is_terminal():
        raise RunNotTerminal(f"{record.run_id} has neither reported nor refused")
    attempt = record.attempt()
    if attempt is None:
        raise Unreadable(f"{record.run_id} has no ATTEMPTED entry, so its executor is unknown")
    executor = str(attempt.get("actor") or "")
    if not executor:
        raise Unreadable(f"{record.run_id} attributes its attempt to nobody")
    walk = _Walk()
    walk.cite(attempt)
    payload = attempt.get("payload") or {}

    if candidate_observer_id == executor:
        walk.edge("SAME_ACTOR", attempt)

    if "lease" not in payload:
        walk.cannot_answer("HOLDS_RUN_LEASE")
    else:
        lease = payload["lease"]
        if isinstance(lease, dict) and lease.get("holder_id") == candidate_observer_id:
            walk.edge("HOLDS_RUN_LEASE", attempt)

    if "grant_id" not in payload:
        walk.cannot_answer("GRANT_DESCENDS_FROM_RUN")
    elif payload["grant_id"]:
        _walk_grants(record, candidate_observer_id, str(payload["grant_id"]), walk)

    _walk_outputs(record, candidate_observer_id, walk)

    if walk.found:
        outcome, completeness = "DIRECT", "COMPLETE"
    elif walk.unanswerable:
        outcome, completeness = "UNDETERMINED", "INCOMPLETE"
    else:
        outcome, completeness = "INDEPENDENT", "COMPLETE"

    material = f"{record.run_id}|{candidate_observer_id}|{inferred_at}".encode("utf-8")
    inference = {
        "inference_id": "urn:soveraeign:observation:relation-inference:"
                        + hashlib.sha256(material).hexdigest()[:24],
        "run_id": record.run_id,
        "candidate_observer_id": candidate_observer_id,
        "candidate_observer_kind": candidate_observer_kind,
        "executor_id": executor,
        "edges_examined": list(EDGES),
        "edges_found": walk.found,
        "record_completeness": completeness,
        "outcome": outcome,
        "evidence_addresses": [RunRecord.address_of(entry) for entry in walk.read],
        "evidence_digests": [RunRecord.digest_of(entry) for entry in walk.read],
        "inferred_at": inferred_at,
    }
    if walk.unanswerable:
        inference["unanswerable_edges"] = list(walk.unanswerable)
    return inference


def require_independent(inference: dict[str, Any], observer_id: str) -> None:
    """Refuse unless this inference admits this observer."""
    if inference.get("candidate_observer_id") != observer_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('candidate_observer_id')}, not {observer_id}")
    outcome = inference.get("outcome")
    if outcome == "UNDETERMINED":
        raise RelationUndetermined(
            "the record could not answer: " + ", ".join(inference.get("unanswerable_edges", [])))
    if outcome != "INDEPENDENT" or inference.get("edges_found"):
        edges = ", ".join(found["edge"] for found in inference.get("edges_found", []))
        raise ObserverNotIndependent(f"{observer_id} is joined to the run by {edges or outcome}")


__all__ = ["EDGES", "infer_relation", "require_independent"]
