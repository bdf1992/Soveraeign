"""Infer whether a candidate observer is independent of a subject, from the record alone.

`decisions/0041-the-observation-service.md`, Ruling 2: nobody declares their own independence.
`decisions/0104-independence-is-context-and-perspective.md` says what independence is, on two
axes that do not substitute for one another.

**Context** is what the observer was given. An observer may hold what the run was asked to do
and what it produced; it may not hold how the run decided, what it concluded, or what it says
about itself. Ends, not means. That axis is removable at launch, and the launcher declares
what it passed.

**Perspective** is what the observer is. A session holding none of the prior session's
transcript is not a stranger to it - it is a version of the prior actor, loading the same
profile and reading the artifact the way the builder read it. Isolating context removes what
an observer inherited, never what it is. That axis is removable only by being a different
actor, and it is read from the operating profile rather than the actor id.

The walk is scoped to the subject's standing lifecycle, not to one run. Standing moves
`OPEN -> BUILT -> WITNESSED -> RATIFIED` and a subject collects actors along the way, so a
per-run walk would admit a builder as its own witness one arrow later.

One edge found is `DIRECT`. None found over a record that answered every edge is
`INDEPENDENT`. A record that could not answer an edge is `UNDETERMINED`, which refuses:
absence of a recorded edge is not absence of a relation.

A found edge answers the question the inference asks, so a record that shows the candidate
executing the run reads `DIRECT` even when another edge could not be examined. Only a record
that found nothing and could not answer everything reads `UNDETERMINED`. That precedence is a
default taken here: it refuses in both cases, and it keeps the refusal's name honest.
"""

from __future__ import annotations

from typing import Any
import hashlib

from .errors import ObserverNotIndependent, RelationUndetermined, RunNotTerminal, Unreadable
from .record import CONSTRUCTION_CONTEXT, RunRecord

EDGES = (
    "SAME_ACTOR_VERSION",
    "PRIOR_STANDING_ACTOR",
    "HOLDS_RUN_LEASE",
    "PRODUCED_THE_OUTPUT",
    "ONLY_EXECUTOR_REPORT",
    "CONSTRUCTION_CONTEXT_INHERITED",
    "PREDICATES_SUPPLIED_BY_EXECUTOR",
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


def _same_version(record: RunRecord, candidate: str, actor: str) -> bool:
    """Is the candidate a version of this actor: the same actor, or the same loaded profile?"""
    if candidate == actor:
        return True
    theirs = record.profile_of(actor)
    return theirs is not None and theirs == record.profile_of(candidate)


def _walk_perspective(record: RunRecord, candidate: str, walk: _Walk) -> None:
    """Is the candidate a version of an actor that executed this run?

    A profile the record does not carry for either side is a question it cannot answer. The
    candidate being an executor outright is answerable without any profile at all.
    """
    executors = record.executors()
    for actor, entry in executors.items():
        if _same_version(record, candidate, actor):
            walk.edge("SAME_ACTOR_VERSION", entry)
            return
    if record.profile_of(candidate) is None or any(
            record.profile_of(actor) is None for actor in executors):
        walk.cannot_answer("SAME_ACTOR_VERSION")


def _walk_lifecycle(record: RunRecord, candidate: str, walk: _Walk) -> None:
    """Did the candidate, or a version of it, already move this subject along an arrow?

    Without a subject the run belongs to, there is no lifecycle to walk and the edge is
    unanswerable. That is the shape a per-run inference had for every subject.
    """
    subject = record.subject_id()
    if subject is None:
        walk.cannot_answer("PRIOR_STANDING_ACTOR")
        return
    arrows = record.standings(subject)
    if not arrows:
        walk.cannot_answer("PRIOR_STANDING_ACTOR")
        return
    walk.cite(*arrows)
    for entry in arrows:
        if _same_version(record, candidate, str(entry.get("actor") or "")):
            walk.edge("PRIOR_STANDING_ACTOR", entry)
            return


def _walk_context(record: RunRecord, candidate: str, walk: _Walk) -> None:
    """What was the candidate handed, and who wrote the criteria it grades against?

    Both answers come from the launcher's own entry. The observer never declares either, and
    a launch the record does not carry answers neither.
    """
    launch = record.launches().get(candidate)
    if launch is None:
        walk.cannot_answer("CONSTRUCTION_CONTEXT_INHERITED")
        walk.cannot_answer("PREDICATES_SUPPLIED_BY_EXECUTOR")
        return
    walk.cite(launch)
    payload = launch.get("payload") or {}

    passed = payload.get("context_passed")
    if not isinstance(passed, list):
        walk.cannot_answer("CONSTRUCTION_CONTEXT_INHERITED")
    elif any(str(kind) in CONSTRUCTION_CONTEXT for kind in passed):
        walk.edge("CONSTRUCTION_CONTEXT_INHERITED", launch)

    author = payload.get("predicates_source_actor")
    if not author:
        walk.cannot_answer("PREDICATES_SUPPLIED_BY_EXECUTOR")
    elif any(_same_version(record, str(author), actor) for actor in record.executors()):
        walk.edge("PREDICATES_SUPPLIED_BY_EXECUTOR", launch)


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


def _digests(entries: list[dict[str, Any]]) -> list[str]:
    """Entry digests, or `UNREADABLE`: an inference that cannot cite what it read has not read."""
    try:
        return [RunRecord.digest_of(entry) for entry in entries]
    except ValueError as error:
        raise Unreadable(str(error)) from error


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
    unreadable = record.malformed()
    if unreadable is not None:
        raise Unreadable(unreadable)
    if not record.is_terminal():
        raise RunNotTerminal(f"{record.run_id} has neither reported nor refused")
    attempts = record.attempts()
    if not attempts:
        raise Unreadable(f"{record.run_id} has no ATTEMPTED entry, so its executor is unknown")
    executor = str(attempts[0].get("actor"))
    walk = _Walk()
    walk.cite(*attempts, *record.executors().values())

    _walk_perspective(record, candidate_observer_id, walk)
    _walk_lifecycle(record, candidate_observer_id, walk)
    _walk_context(record, candidate_observer_id, walk)

    # Every attempt ran under its own lease; a retry's lessee is as direct as the first
    # attempt's, so each attempt is read, not only the earliest.
    for attempt in attempts:
        payload = attempt.get("payload") or {}
        if "lease" not in payload:
            walk.cannot_answer("HOLDS_RUN_LEASE")
        else:
            lease = payload["lease"]
            if isinstance(lease, dict) and lease.get("holder_id") == candidate_observer_id:
                walk.edge("HOLDS_RUN_LEASE", attempt)

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
        "evidence_digests": _digests(walk.read),
        "inferred_at": inferred_at,
    }
    subject = record.subject_id()
    if subject is not None:
        inference["subject_id"] = subject
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
