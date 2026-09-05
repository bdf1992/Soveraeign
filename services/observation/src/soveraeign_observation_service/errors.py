"""Refusals the Observation Service declares in `contracts/service.json`.

Every refusal carries the reason code the manifest names, so a receipt records the same word
the contract promised. A refusal is a result, not an exception in the crash sense: the façade
in `service.py` catches these, writes the receipt, and re-raises.
"""

from __future__ import annotations


class ObservationRefused(Exception):
    """Base of every declared refusal. `reason_code` is the manifest's word."""

    reason_code = "MISSING_PRECONDITION"

    def __init__(self, detail: str) -> None:
        super().__init__(f"{self.reason_code}: {detail}")
        self.detail = detail


class RunNotTerminal(ObservationRefused):
    """The run is still in flight; there is nothing durable to observe yet."""

    reason_code = "RUN_NOT_TERMINAL"


class RelationUndetermined(ObservationRefused):
    """The run's record could not answer every direct edge, or the inference offered was read
    over another record than the one being observed. Silence is not a pass."""

    reason_code = "RELATION_UNDETERMINED"


class ObserverNotIndependent(ObservationRefused):
    """A direct edge joins the candidate to the run; it may not observe it."""

    reason_code = "OBSERVER_NOT_INDEPENDENT"


class PredicatesUndeclared(ObservationRefused):
    """No usable predicate declaration preceded the looking."""

    reason_code = "PREDICATES_UNDECLARED"


class Unreadable(ObservationRefused):
    """A durable output, or the run's record, could not be read."""

    reason_code = "UNREADABLE"


class DigestMismatch(ObservationRefused):
    """The bytes read do not carry the digest the record declares for them."""

    reason_code = "DIGEST_MISMATCH"


class ObservationMissing(ObservationRefused):
    """No observation with that address has been recorded."""

    reason_code = "OBSERVATION_MISSING"


class IncompleteProposal(ObservationRefused):
    """A request or declaration omits a field the contract requires."""

    reason_code = "INCOMPLETE_PROPOSAL"


__all__ = [
    "DigestMismatch",
    "IncompleteProposal",
    "ObservationMissing",
    "ObservationRefused",
    "ObserverNotIndependent",
    "PredicatesUndeclared",
    "RelationUndetermined",
    "RunNotTerminal",
    "Unreadable",
]
