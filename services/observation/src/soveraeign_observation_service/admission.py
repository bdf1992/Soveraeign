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

So the record is a parameter, and the verdict is re-derived from it rather than believed:
`inference_id` is recomputed from the material the walk hashes, and every address the
inference says it read must be an entry the record actually carries.
"""

from __future__ import annotations

from typing import Any
import hashlib

from .errors import ObserverNotIndependent, RelationUndetermined
from .record import RunRecord
from .relation import EDGES


def _rederive_id(inference: dict[str, Any]) -> str:
    """The inference id `relation.infer_relation` would have minted for this subject."""
    material = (f"{inference.get('run_id')}|{inference.get('candidate_observer_id')}"
                f"|{inference.get('inferred_at')}").encode("utf-8")
    return ("urn:soveraeign:observation:relation-inference:"
            + hashlib.sha256(material).hexdigest()[:24])


def require_independent(inference: dict[str, Any], observer_id: str, run_id: str | None = None,
                        record: RunRecord | None = None) -> None:
    """Refuse unless this inference admits this observer for this run, over this record."""
    if inference.get("candidate_observer_id") != observer_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('candidate_observer_id')}, not {observer_id}")
    if run_id is not None and inference.get("run_id") != run_id:
        raise RelationUndetermined(
            f"the inference is about {inference.get('run_id')}, not {run_id}")
    if inference.get("inference_id") != _rederive_id(inference):
        raise RelationUndetermined(
            "the inference id does not follow from its own subject, observer and moment; "
            "it was not minted by the walk")
    if record is not None:
        known = {RunRecord.address_of(entry) for entry in record.entries}
        unknown = [address for address in inference.get("evidence_addresses") or []
                   if address not in known]
        if unknown:
            raise RelationUndetermined(
                "the inference cites entries this record does not carry: " + ", ".join(unknown))

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
