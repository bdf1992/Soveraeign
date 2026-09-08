"""Grade an inference before an observation is built on it.

`relation.py` produces a verdict from a record. This module decides whether a verdict handed
back later still admits its observer, which is a different question with a different failure
mode: the inference may not be the one this run and this observer need, and it may have been
written by something other than the walk.

An independent witness found this reading trusting the `outcome` field alone. An inference
saying `INDEPENDENT` over an `INCOMPLETE` record, naming edges it could not answer, was
admitted, and the observation then asserted the record was `COMPLETE`. A gate that reads a
verdict without its own evidence is the substitution this service exists to refuse, so the
whole verdict is read here: the subject, the run, the found edges, the unanswered ones, the
completeness, and whether the examination covered the closed set at all.
"""

from __future__ import annotations

from typing import Any

from .errors import ObserverNotIndependent, RelationUndetermined
from .relation import EDGES


def require_independent(inference: dict[str, Any], observer_id: str, run_id: str | None = None,
                        ) -> None:
    """Refuse unless this inference admits this observer for this run."""
    if inference.get("candidate_observer_id") != observer_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('candidate_observer_id')}, not {observer_id}")
    if run_id is not None and inference.get("run_id") != run_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('run_id')}, not {run_id}")

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
