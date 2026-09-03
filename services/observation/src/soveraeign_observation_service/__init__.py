"""Observation Service: independent observation of runs, independence inferred from the record.

Thin slice under `decisions/0041-the-observation-service.md`: `request-observation`,
`declare-predicates`, `infer-relation`, `observe-run`, and `read-observation`. It reads journal
entries and never writes the journal; it emits observations and never settles a run.
"""

from __future__ import annotations

from .errors import (
    DigestMismatch,
    IncompleteProposal,
    ObservationMissing,
    ObservationRefused,
    ObserverNotIndependent,
    PredicatesUndeclared,
    RelationUndetermined,
    RunNotTerminal,
    Unreadable,
)
from .observe import PREDICATE_KINDS, declare_predicates, observe_run
from .record import RunRecord
from .relation import EDGES, infer_relation
from .service import ObservationService

__all__ = [
    "DigestMismatch",
    "EDGES",
    "IncompleteProposal",
    "ObservationMissing",
    "ObservationRefused",
    "ObservationService",
    "ObserverNotIndependent",
    "PREDICATE_KINDS",
    "PredicatesUndeclared",
    "RelationUndetermined",
    "RunNotTerminal",
    "RunRecord",
    "Unreadable",
    "declare_predicates",
    "infer_relation",
    "observe_run",
]
