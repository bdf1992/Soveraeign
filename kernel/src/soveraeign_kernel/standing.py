"""Standing transitions: submit, admit, ratify, attest, make effective, retract.

Each method is one row of the ``SPEC.md`` Transition contract. The standing
ladder ``RECORDED -> ADMITTED -> RATIFIED -> EFFECTIVE`` is climbed one rung per
transition against the exact pre-state the caller declares; no rung is skipped
and none is rewritten. Retraction clears current effectiveness through a
counter-record and leaves every rung on record (C4, C9).
"""

from __future__ import annotations

from typing import Any

from . import reasons
from .base import KernelBase
from .records import ATTESTATION_OUTCOMES, AUTHORITY_TYPES, Attestation, CounterRecord, Record

PROPOSAL_FIELDS = ("actor_id", "actor_kind", "content_address", "source_addresses",
                   "input_digests", "cost_record", "required_authority_type", "scope")


class StandingTransitions(KernelBase):
    """Mixin realizing the standing rows of the transition contract."""

    def _record_inputs(self, record_id: str) -> list[dict[str, str]]:
        return [{"address": record_id, "digest": self.state_digest(record_id) or "sha256:absent"}]

    def submit_proposal(self, *, actor_id: str, actor_kind: str, content_address: str = "",
                        source_addresses: list[str] | None = None,
                        input_digests: list[str] | None = None,
                        cost_record: dict[str, Any] | None = None,
                        required_authority_type: str = "", scope: str = "") -> dict[str, Any]:
        """Record a proposal. It claims no authority and begins ``RECORDED``."""
        fields = {"actor_id": actor_id, "actor_kind": actor_kind,
                  "content_address": content_address, "source_addresses": source_addresses,
                  "input_digests": input_digests, "cost_record": cost_record,
                  "required_authority_type": required_authority_type, "scope": scope}
        declared_input = {"address": content_address or "urn:soveraeign:absent",
                          "digest": input_digests[0] if input_digests else "sha256:absent"}
        attempt = self.attempt("submit_proposal", actor_id=actor_id, actor_kind=actor_kind,
                               inputs=[declared_input])
        missing = [name for name in PROPOSAL_FIELDS if fields[name] in (None, "", [], {})]
        if not attempt.check("proposal_complete", not missing, missing=missing):
            return attempt.refuse(reasons.INCOMPLETE_PROPOSAL, f"missing {', '.join(missing)}")
        if not attempt.check("authority_type_declared",
                             required_authority_type in AUTHORITY_TYPES):
            return attempt.refuse(reasons.INCOMPLETE_PROPOSAL, "unknown required authority type")
        record = Record(record_id=self.new_id("record"), created_at=self.timestamp(), **fields)
        self.records[record.record_id] = record
        self.journal.append("RECORD", record.to_dict())
        return attempt.commit(reason="proposal recorded without authority",
                              emitted=[record.record_id])

    def admit(self, record_id: str, *, actor_id: str, actor_kind: str, expected_state: str | None,
              predicate_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Add ``ADMITTED`` when every admission predicate passed against the exact state."""
        attempt = self.attempt("admit", actor_id=actor_id, actor_kind=actor_kind,
                               inputs=self._record_inputs(record_id))
        record = self.records.get(record_id)
        if not attempt.check("record_present", record is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such record")
        if not attempt.check_pre_state(expected_state, self.state_digest(record_id)):
            return attempt.refuse(reasons.STALE_STATE, "declared pre-state is not current")
        if not attempt.check("standing_is_recorded", record.standing == "RECORDED"):
            return attempt.refuse(reasons.STANDING_REFUSED, f"record is {record.standing}")
        attempt.preconditions.extend(predicate_results)
        if not all(item.get("result") is True for item in predicate_results):
            return attempt.refuse(reasons.ADMISSION_REFUSED, "an admission predicate failed")
        record.standing_history.append("ADMITTED")
        return attempt.commit(reason="admission predicates passed", emitted=[record_id])

    def ratify(self, record_id: str, *, actor_id: str, actor_kind: str, expected_state: str | None,
               grant_id: str | None) -> dict[str, Any]:
        """Add ``RATIFIED`` under a live grant of the claim's required authority type."""
        attempt = self.attempt("ratify", actor_id=actor_id, actor_kind=actor_kind,
                               inputs=self._record_inputs(record_id),
                               grant_ids=[grant_id] if grant_id else [])
        record = self.records.get(record_id)
        if not attempt.check("record_present", record is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such record")
        if not attempt.check_pre_state(expected_state, self.state_digest(record_id)):
            return attempt.refuse(reasons.STALE_STATE, "declared pre-state is not current")
        if not attempt.check("standing_is_admitted", record.standing == "ADMITTED"):
            return attempt.refuse(reasons.STANDING_REFUSED, f"record is {record.standing}")
        if not attempt.check_authority(grant_id, authority_type=record.required_authority_type,
                                       capability="ratify", scope=record.scope):
            return attempt.refuse(reasons.AUTHORITY_REFUSED, "no live matching grant")
        record.standing_history.append("RATIFIED")
        return attempt.commit(reason=f"ratified under {grant_id}", emitted=[record_id])

    def attest(self, claim_id: str, *, validator_id: str, validator_version: str,
               input_addresses: list[str], input_digests: list[str], run_id: str | None,
               outcome: str, evidence_addresses: list[str]) -> dict[str, Any]:
        """Record one attestation outcome. It changes no standing and no authority (C5)."""
        attempt = self.attempt("attest", actor_id=validator_id or "urn:soveraeign:absent",
                               actor_kind="SYSTEM", inputs=self._record_inputs(claim_id))
        record = self.records.get(claim_id)
        if not attempt.check("record_present", record is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such claim")
        if not attempt.check("claim_ratified", "RATIFIED" in record.standing_history):
            return attempt.refuse(reasons.STANDING_REFUSED, "claim is not ratified")
        declared = bool(validator_id and validator_version and input_digests)
        if not attempt.check("validator_declared", declared):
            return attempt.refuse(reasons.VALIDATOR_UNDECLARED, "validator or inputs undeclared")
        if not attempt.check("outcome_known", outcome in ATTESTATION_OUTCOMES):
            return attempt.refuse(reasons.VALIDATOR_UNDECLARED, f"unknown outcome {outcome}")
        attestation = Attestation(
            attestation_id=self.new_id("attestation"), claim_id=claim_id,
            validator_id=validator_id, validator_version=validator_version,
            input_addresses=input_addresses, input_digests=input_digests, run_id=run_id,
            outcome=outcome, evidence_addresses=evidence_addresses, created_at=self.timestamp())
        self.attestations[attestation.attestation_id] = attestation
        self.journal.append("ATTESTATION", attestation.to_dict())
        return attempt.commit(reason=f"attestation {outcome}", emitted=[attestation.attestation_id],
                              evidence=evidence_addresses)

    def make_effective(self, record_id: str, *, actor_id: str, actor_kind: str,
                       expected_state: str | None) -> dict[str, Any]:
        """Add ``EFFECTIVE`` when an attestation over the claim's exact inputs reproduced it.

        Attestations over other inputs are not evidence for this state: a changed input
        cannot inherit ``REPRODUCED`` (PROD-I-8), so the gate reads ``UNATTESTABLE``.
        """
        attempt = self.attempt("make_effective", actor_id=actor_id, actor_kind=actor_kind,
                               inputs=self._record_inputs(record_id))
        record = self.records.get(record_id)
        if not attempt.check("record_present", record is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such record")
        if not attempt.check_pre_state(expected_state, self.state_digest(record_id)):
            return attempt.refuse(reasons.STALE_STATE, "declared pre-state is not current")
        if not attempt.check("standing_is_ratified", record.standing == "RATIFIED"):
            return attempt.refuse(reasons.STANDING_REFUSED, f"record is {record.standing}")
        if not attempt.check("no_current_counter", not record.countered_by):
            return attempt.refuse(reasons.POLICY_REFUSED, "record is countered")
        applicable = [item for item in self.attestations.values()
                      if item.claim_id == record_id and item.input_digests == record.input_digests]
        outcomes = {item.outcome for item in applicable}
        if not attempt.check("no_dissent", "DISSENTED" not in outcomes):
            return attempt.refuse(reasons.DISSENTED, "a validator dissented on these inputs")
        if not attempt.check("reproduced_on_exact_inputs", "REPRODUCED" in outcomes):
            return attempt.refuse(reasons.UNATTESTABLE, "no reproduction over the exact inputs")
        record.standing_history.append("EFFECTIVE")
        record.effective = True
        return attempt.commit(reason="reproduced on exact inputs; no counter", emitted=[record_id],
                              evidence=[item.attestation_id for item in applicable])

    def retract(self, record_id: str, *, actor_id: str, actor_kind: str, grant_id: str | None,
                reason: str, effect_class: str = "RECORD_LOCAL",
                not_reversed: str | None = None) -> dict[str, Any]:
        """Counter a record. History stays; only current effectiveness changes (C9)."""
        attempt = self.attempt("retract", actor_id=actor_id, actor_kind=actor_kind,
                               inputs=self._record_inputs(record_id), effect_class=effect_class,
                               grant_ids=[grant_id] if grant_id else [])
        record = self.records.get(record_id)
        if not attempt.check("record_present", record is not None):
            return attempt.refuse(reasons.TARGET_UNKNOWN, "no such record")
        if not attempt.check_authority(grant_id, authority_type=record.required_authority_type,
                                       capability="retract", scope=record.scope):
            return attempt.refuse(reasons.AUTHORITY_REFUSED, "no live retraction grant")
        if effect_class != "RECORD_LOCAL" and not attempt.check("consumption_named",
                                                                bool(not_reversed)):
            return attempt.refuse(reasons.POLICY_REFUSED, "non-local retraction must name "
                                  "what remains consumed or changed")
        target_receipt = self._last_receipt_for(record_id)
        counter = CounterRecord(
            counter_record_id=self.new_id("counter"), target_record_id=record_id,
            target_receipt_id=target_receipt, actor_id=actor_id, authority_grant_id=grant_id,
            reason=reason, effect_class=effect_class, not_reversed=not_reversed,
            created_at=self.timestamp())
        self.counters[counter.counter_record_id] = counter
        self.journal.append("COUNTER", counter.to_dict())
        record.effective = False
        record.countered_by.append(counter.counter_record_id)
        return attempt.commit(outcome="COUNTERED", phase="COUNTERED", reason=reason,
                              emitted=[counter.counter_record_id], prior_receipt_id=target_receipt)

    def _last_receipt_for(self, record_id: str) -> str:
        for receipt in reversed(list(self.receipts.values())):
            if record_id in receipt["input_addresses"] and receipt["outcome"] == "COMMITTED":
                return receipt["receipt_id"]
        return "urn:soveraeign:receipt:absent"
