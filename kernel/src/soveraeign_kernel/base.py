"""Kernel state, clocks, identifiers, pre-state digests, and the attempt envelope.

Every transition the kernel realizes runs through ``Attempt``: open it with the
declared actor, inputs, authority, and effect class; add precondition results;
then close it exactly once with ``refuse`` or ``commit``. Closing appends one
``EventEnvelope`` and one ``Receipt`` to the journal. There is no other way to
put an event or receipt on record, which is how "exactly one terminal receipt per
attempted transition" is kept by construction rather than by discipline.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable
import itertools
import uuid

from .authority import authorized, evaluate
from .digests import digest_of
from .journal import Journal
from .records import (
    KERNEL_TRANSITIONS, LEGAL_TRANSITIONS, Attestation, AuthorityGrant, CounterRecord,
    Observation, Record, Run,
)

DEFAULT_INTERFACE = "urn:soveraeign:interface:kernel-python-v1"
STANDING_TRANSITIONS = ("submit_proposal", "admit", "ratify", "make_effective")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid_ids(prefix: str) -> str:
    return f"urn:soveraeign:{prefix}:{uuid.uuid4()}"


def sequential_ids() -> Callable[[str], str]:
    """Deterministic identifier factory for tests and fixtures."""
    counters: dict[str, itertools.count] = {}

    def next_id(prefix: str) -> str:
        return f"urn:soveraeign:{prefix}:{next(counters.setdefault(prefix, itertools.count(1)))}"

    return next_id


class Attempt:
    """One attempted transition; closes exactly once with a terminal receipt."""

    def __init__(self, kernel: KernelBase, transition: str, *, actor_id: str, actor_kind: str,
                 operation_id: str, inputs: list[dict[str, str]], effect_class: str,
                 grant_ids: list[str], interface_id: str) -> None:
        self.kernel = kernel
        self.transition = transition
        self.actor_id, self.actor_kind = actor_id, actor_kind
        self.operation_id, self.inputs = operation_id, inputs
        self.effect_class, self.grant_ids = effect_class, grant_ids
        self.interface_id = interface_id
        self.preconditions: list[dict[str, Any]] = []
        self.closed = False

    def check(self, predicate: str, result: bool, **detail: Any) -> bool:
        self.preconditions.append({"predicate": predicate, "result": bool(result), **detail})
        return bool(result)

    def check_pre_state(self, expected: str | None, actual: str) -> bool:
        """A caller that declares no pre-state is refused: "exact pre-state" is an input."""
        return self.check("pre_state_current", expected == actual, expected=expected, actual=actual)

    def check_authority(self, grant_id: str | None, *, authority_type: str, capability: str,
                        scope: str) -> bool:
        grant = self.kernel.grants.get(grant_id) if grant_id else None
        results = evaluate(grant, actor_id=self.actor_id, authority_type=authority_type,
                           capability=capability, scope=scope, now=self.kernel.now(),
                           spent=self.kernel.spent(grant_id) if grant_id else 0)
        self.preconditions.extend(results)
        return authorized(results)

    def refuse(self, reason_code: str, reason: str) -> dict[str, Any]:
        return self._close("REFUSED", "REFUSED", "SETTLED", reason, reason_code, [], [], [], None)

    def commit(self, *, outcome: str = "COMMITTED", event_outcome: str | None = None,
               phase: str = "SETTLED", reason: str, reason_code: str | None = None,
               outputs: list[dict[str, str]] | None = None, emitted: list[str] | None = None,
               evidence: list[str] | None = None, prior_receipt_id: str | None = None,
               ) -> dict[str, Any]:
        return self._close(outcome, event_outcome or outcome, phase, reason, reason_code,
                           outputs or [], emitted or [], evidence or [], prior_receipt_id)

    def _close(self, outcome: str, event_outcome: str, phase: str, reason: str,
               reason_code: str | None, outputs: list[dict[str, str]], emitted: list[str],
               evidence: list[str], prior_receipt_id: str | None) -> dict[str, Any]:
        if self.closed:
            raise RuntimeError(f"{self.transition}: attempt already closed")
        self.closed = True
        kernel, created_at = self.kernel, self.kernel.timestamp()
        event_id, receipt_id = kernel.new_id("event"), kernel.new_id("receipt")
        receipt = {
            "receipt_id": receipt_id, "event_id": event_id, "event_type": self.transition,
            "actor_id": self.actor_id, "interface_id": self.interface_id,
            "input_addresses": [item["address"] for item in self.inputs],
            "input_state_digest": digest_of(self.inputs),
            "authority_grant_ids": list(self.grant_ids),
            "precondition_results": self.preconditions, "effect_class": self.effect_class,
            "outcome": outcome, "reason_code": reason_code, "emitted_record_addresses": emitted,
            "observed_evidence_addresses": evidence, "prior_receipt_id": prior_receipt_id,
            "created_at": created_at,
        }
        receipt["receipt_digest"] = digest_of(receipt)
        event = {
            "event_id": event_id, "operation_id": self.operation_id, "event_phase": phase,
            "actor_id": self.actor_id, "actor_kind": self.actor_kind, "reason": reason,
            "occurred_at": created_at, "inputs": self.inputs, "outputs": outputs,
            "authority_grant_ids": list(self.grant_ids), "effect_class": self.effect_class,
            "outcome": event_outcome, "receipt_id": receipt_id,
        }
        kernel.journal.append("EVENT", event)
        kernel.journal.append("RECEIPT", receipt)
        kernel.receipts[receipt_id] = receipt
        return receipt


class KernelBase:
    """Projections of the journal plus the clocks and identifiers every transition uses."""

    def __init__(self, clock: Callable[[], datetime] | None = None,
                 id_factory: Callable[[str], str] | None = None,
                 interface_id: str = DEFAULT_INTERFACE) -> None:
        self._clock = clock or _utc_now
        self._ids = id_factory or _uuid_ids
        self.interface_id = interface_id
        self.journal = Journal()
        self.grants: dict[str, AuthorityGrant] = {}
        self.records: dict[str, Record] = {}
        self.attestations: dict[str, Attestation] = {}
        self.runs: dict[str, Run] = {}
        self.observations: dict[str, Observation] = {}
        self.counters: dict[str, CounterRecord] = {}
        self.receipts: dict[str, dict[str, Any]] = {}

    def now(self) -> datetime:
        return self._clock()

    def timestamp(self) -> str:
        return self.now().isoformat().replace("+00:00", "Z")

    def new_id(self, prefix: str) -> str:
        return self._ids(prefix)

    @staticmethod
    def transitions() -> dict[str, list[str]]:
        """The one list of legal operations every binding discovers (SPEC.md parity)."""
        return {"legal": list(LEGAL_TRANSITIONS), "realized_by_kernel": list(KERNEL_TRANSITIONS)}

    def register_grant(self, grant: AuthorityGrant) -> AuthorityGrant:
        """Place a grant on record. Issuing authority is O3's open question; this records only."""
        self.grants[grant.grant_id] = grant
        self.journal.append("GRANT", grant.to_dict())
        return grant

    def spent(self, grant_id: str) -> int:
        return sum(1 for receipt in self.receipts.values()
                   if grant_id in receipt["authority_grant_ids"]
                   and receipt["outcome"] in ("COMMITTED", "COUNTERED"))

    def state_digest(self, record_id: str) -> str | None:
        record = self.records.get(record_id)
        return digest_of(record.to_dict()) if record else None

    def run_state_digest(self, run_id: str) -> str | None:
        run = self.runs.get(run_id)
        return digest_of(run.to_dict()) if run else None

    def attempt(self, transition: str, *, actor_id: str, actor_kind: str,
                inputs: list[dict[str, str]], effect_class: str = "RECORD_LOCAL",
                grant_ids: list[str] | None = None, operation_id: str | None = None,
                interface_id: str | None = None) -> Attempt:
        return Attempt(self, transition, actor_id=actor_id, actor_kind=actor_kind,
                       operation_id=operation_id or self.new_id("operation"), inputs=inputs,
                       effect_class=effect_class, grant_ids=grant_ids or [],
                       interface_id=interface_id or self.interface_id)

    def audit(self) -> list[str]:
        """Journal defects plus any record whose projection disagrees with the journal."""
        defects = self.journal.audit()
        history: dict[str, list[str]] = {}
        effective: dict[str, bool] = {}
        for receipt in self.journal.bodies("RECEIPT"):
            if receipt["outcome"] not in ("COMMITTED", "COUNTERED"):
                continue
            addresses = (receipt["emitted_record_addresses"]
                         if receipt["event_type"] == "submit_proposal"
                         else receipt["input_addresses"])
            target = addresses[0] if addresses else None
            if target is None:
                continue
            if receipt["event_type"] in STANDING_TRANSITIONS:
                standing = {"submit_proposal": "RECORDED", "admit": "ADMITTED",
                            "ratify": "RATIFIED", "make_effective": "EFFECTIVE"}
                history.setdefault(target, []).append(standing[receipt["event_type"]])
                effective[target] = receipt["event_type"] == "make_effective"
            elif receipt["event_type"] == "retract":
                effective[target] = False
        for record_id, record in self.records.items():
            if record.standing_history != history.get(record_id, []):
                defects.append(f"record {record_id}: standing projection diverges from journal")
            if record.effective != effective.get(record_id, False):
                defects.append(f"record {record_id}: effectiveness diverges from journal")
        return defects
