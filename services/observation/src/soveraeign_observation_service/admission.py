"""Grade an inference before an observation is built on it.

`relation.py` produces a verdict from a record. This module decides whether a verdict handed
back later still admits its observer, which is a different question with a different failure
mode: the inference may not be the one this run and this observer need, and it may have been
written by something other than the walk.

One witness pass found this reading trusting the `outcome` field alone: an inference saying
`INDEPENDENT` over an `INCOMPLETE` record, naming edges it could not answer, was admitted, and
the observation then asserted the record was `COMPLETE`. The next pass found the repair still
grading only fields of the same declaration, and drove the run's own executor through the
exported `observe_run` on a hand-written dict. A gate that reads a report about the walk where
it could read the walk is the substitution this service exists to refuse.

A third pass then defeated that repair. Recomputing `inference_id` from the run, the observer
and the moment proves nothing: those are three fields the caller supplies and two of them are
compared here anyway, so the id is identical for every verdict the walk could return about one
subject. The executor drove its own run through this gate on a correctly hashed forgery.

So the verdict is not re-derived from its own fields. It is **re-walked**: this module runs
`infer_relation` over the record it was handed and refuses unless the handed inference agrees
with what the walk actually finds. A verdict is then a convenience for the caller and never a
credential, which is the only shape that cannot be forged by a caller who has read this file.
"""

from __future__ import annotations

from typing import Any

from .errors import ObserverNotIndependent, RelationUndetermined
from .record import RunRecord
from .relation import EDGES, infer_relation

#: What a handed inference must agree with the walk about. `inferred_at` is excluded because a
#: caller may legitimately hold an older reading of an append-only record; every field that
#: decides admission is here.
GRADED = ("run_id", "candidate_observer_id", "executor_id", "subject_id", "outcome",
          "record_completeness", "edges_examined", "edges_found", "unanswerable_edges",
          "evidence_addresses", "evidence_digests", "inference_id")


def _rewalk(inference: dict[str, Any], record: RunRecord) -> None:
    """Run the walk again and refuse unless the handed verdict is the one it reaches."""
    walked = infer_relation(record, str(inference.get("candidate_observer_id") or ""),
                            str(inference.get("candidate_observer_kind") or "MODEL"),
                            str(inference.get("inferred_at") or ""))
    disagreed = [field for field in GRADED
                 if inference.get(field) != walked.get(field)]
    if disagreed:
        raise RelationUndetermined(
            "the inference disagrees with the walk over this record on "
            + ", ".join(disagreed) + "; a verdict is not a credential")


def require_independent(inference: dict[str, Any], observer_id: str, run_id: str | None = None,
                        record: RunRecord | None = None) -> None:
    """Refuse unless this inference admits this observer for this run, over this record."""
    if inference.get("candidate_observer_id") != observer_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('candidate_observer_id')}, not {observer_id}")
    if run_id is not None and inference.get("run_id") != run_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('run_id')}, not {run_id}")
    if record is not None:
        _rewalk(inference, record)

    # A found edge answers the question the inference asks, so it is read before completeness:
    # the same precedence `infer_relation` documents, and the reason `DIRECT` may carry an
    # unanswered edge while `INDEPENDENT` may not.
    found = inference.get("edges_found") or []
    if found:
        raise ObserverNotIndependent(
            f"{observer_id} is joined to the run by "
            + ", ".join(edge["edge"] for edge in found))
    unanswered = inference.get("unanswerable_edges") or []
    outcome = inference.get("outcome")
    if outcome == "UNDETERMINED" or unanswered:
        raise RelationUndetermined("the record could not answer: " + (", ".join(unanswered)
                                                                     or "no edge was named"))
    if inference.get("record_completeness") != "COMPLETE":
        raise RelationUndetermined(
            f"the record reads {inference.get('record_completeness')!r}, not COMPLETE")
    missing = [edge for edge in EDGES if edge not in (inference.get("edges_examined") or [])]
    if missing:
        raise RelationUndetermined(
            "the inference did not examine " + ", ".join(missing)
            + "; a narrowed examination reaches independence by not looking")
    if outcome != "INDEPENDENT":
        raise ObserverNotIndependent(f"{observer_id} is joined to the run by {outcome}")


__all__ = ["require_independent"]
