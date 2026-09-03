"""The Observation Service façade: five declared operations, one receipt per attempt.

`request-observation`, `declare-predicates`, `infer-relation`, `observe-run`, and
`read-observation` are the thin slice `services/observation/contracts/service.json` declares as
built. `list-pending-observations`, `counter-observation`, and `attest-observation` remain
declared and unbuilt.

State here is the service's own, in memory and append-only: requests, declarations,
inferences, observations, and receipts. It is not the journal - the Record Service owns that
and this service never writes it - and it is not standing. Every attempt, admitted or refused,
leaves exactly one receipt naming the manifest's reason code, which is the invariant issue
#173 lists first among its defeating cases.
"""

from __future__ import annotations

from typing import Any
import hashlib

from . import observe as _observe
from . import relation as _relation
from .errors import (
    IncompleteProposal,
    ObservationMissing,
    ObservationRefused,
    RelationUndetermined,
    RunNotTerminal,
    Unreadable,
)
from .record import RunRecord

ACTOR_KINDS = ("HUMAN", "MODEL", "WORKER", "SYSTEM")


class ObservationService:
    """Own the observation loop for runs whose record is handed in as journal entries."""

    def __init__(self, clock) -> None:
        """`clock` returns the current moment as an ISO-8601 string; injected, never read."""
        self._clock = clock
        self.requests: list[dict[str, Any]] = []
        self.declarations: list[dict[str, Any]] = []
        self.inferences: list[dict[str, Any]] = []
        self.observations: list[dict[str, Any]] = []
        self.receipts: list[dict[str, Any]] = []

    # ---- receipts ---------------------------------------------------------

    def _receipt(self, operation: str, subject: str, outcome: str,
                 reason_code: str | None, detail: str) -> dict[str, Any]:
        material = f"{operation}|{subject}|{len(self.receipts)}".encode("utf-8")
        receipt = {
            "receipt_id": "urn:soveraeign:observation:receipt:"
                          + hashlib.sha256(material).hexdigest()[:24],
            "operation": operation,
            "subject": subject,
            "outcome": outcome,
            "reason_code": reason_code,
            "detail": detail,
            "recorded_at": self._clock(),
        }
        self.receipts.append(receipt)
        return receipt

    def _attempt(self, operation: str, subject: str, commit: str, act):
        """Run one operation; admitted or refused, exactly one receipt is left behind.

        A malformed record (a missing digest, subject, or payload) is not a crash the caller
        should see without a receipt: it is `UNREADABLE`, the refusal the manifest declares
        for a record this service cannot read.
        """
        try:
            result = act()
        except ObservationRefused as refusal:
            self._receipt(operation, subject, "REFUSED", refusal.reason_code, refusal.detail)
            raise
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            refusal = Unreadable(f"{type(error).__name__}: {error}")
            self._receipt(operation, subject, "REFUSED", refusal.reason_code, refusal.detail)
            raise refusal from error
        self._receipt(operation, subject, commit, None, "")
        return result

    # ---- operations -------------------------------------------------------

    def request_observation(self, record: RunRecord, requester_id: str, requester_kind: str,
                            subject: str, proposed_observer_id: str | None = None,
                            ) -> dict[str, Any]:
        """Ask that a terminal run be observed. Asking confers no independence on anyone."""
        def act() -> dict[str, Any]:
            if requester_kind not in ACTOR_KINDS or not requester_id or not subject:
                raise IncompleteProposal("requester, kind, and subject are required")
            if proposed_observer_id == requester_id:
                raise IncompleteProposal("a requester may not nominate itself as observer")
            if not record.is_terminal():
                raise RunNotTerminal(f"{record.run_id} is still in flight")
            addresses = record.reported_addresses()
            if not addresses:
                raise IncompleteProposal("the run reported no durable output to observe")
            material = f"{record.run_id}|{requester_id}".encode("utf-8")
            request = {
                "request_id": "urn:soveraeign:observation:request:"
                              + hashlib.sha256(material).hexdigest()[:24],
                "run_id": record.run_id,
                "subject": subject,
                "requester_id": requester_id,
                "requester_kind": requester_kind,
                "run_outcome": record.terminal_outcome(),
                "durable_output_addresses": addresses,
                "standing": "RECORDED",
                "requested_at": self._clock(),
            }
            if proposed_observer_id:
                request["proposed_observer_id"] = proposed_observer_id
            self.requests.append(request)
            return request
        return self._attempt("request-observation", record.run_id, "RECORDED", act)

    def declare_predicates(self, run_id: str, predicates: list[dict[str, Any]]) -> dict[str, Any]:
        """State what must hold before anyone looks."""
        def act() -> dict[str, Any]:
            declaration = _observe.declare_predicates(run_id, predicates, self._clock())
            self.declarations.append(declaration)
            return declaration
        return self._attempt("declare-predicates", run_id, "COMMITTED", act)

    def infer_relation(self, record: RunRecord, candidate_observer_id: str,
                       candidate_observer_kind: str) -> dict[str, Any]:
        """Walk the run's record for a direct edge. `UNDETERMINED` is recorded and refused."""
        def act() -> dict[str, Any]:
            inference = _relation.infer_relation(record, candidate_observer_id,
                                                 candidate_observer_kind, self._clock())
            self.inferences.append(inference)
            if inference["outcome"] == "UNDETERMINED":
                raise RelationUndetermined(
                    "the record could not answer: " + ", ".join(inference["unanswerable_edges"]))
            return inference
        return self._attempt("infer-relation", record.run_id, "COMMITTED", act)

    def observe_run(self, record: RunRecord, observer_id: str, reader) -> dict[str, Any]:
        """Observe with the latest inference for this observer and the latest declaration."""
        def act() -> dict[str, Any]:
            inference = next((entry for entry in reversed(self.inferences)
                              if entry["run_id"] == record.run_id
                              and entry["candidate_observer_id"] == observer_id), None)
            if inference is None:
                raise RelationUndetermined(f"no relation was inferred for {observer_id}")
            declaration = next((entry for entry in reversed(self.declarations)
                                if entry["run_id"] == record.run_id), None) or {}
            observation = _observe.observe_run(record, inference, declaration, observer_id,
                                               reader, self._clock())
            self.observations.append(observation)
            return observation
        return self._attempt("observe-run", record.run_id, "COMMITTED", act)

    def read_observation(self, observation_id: str) -> dict[str, Any]:
        """The observation with the declaration and inference it was judged through."""
        def act() -> dict[str, Any]:
            observation = next((entry for entry in self.observations
                                if entry["observation_id"] == observation_id), None)
            if observation is None:
                raise ObservationMissing(observation_id)
            run_id, observer = observation["run_id"], observation["observer_id"]
            return {
                "observation": observation,
                "declaration": next((entry for entry in reversed(self.declarations)
                                     if entry["run_id"] == run_id), None),
                "inference": next((entry for entry in reversed(self.inferences)
                                   if entry["run_id"] == run_id
                                   and entry["candidate_observer_id"] == observer), None),
                "receipts": [entry for entry in self.receipts if entry["subject"] == run_id],
            }
        return self._attempt("read-observation", observation_id, "DERIVED", act)


__all__ = ["ACTOR_KINDS", "ObservationService"]
