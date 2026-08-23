"""Kernel audit: what the journal supports versus what the projections say.

The journal is the record; ``Kernel.records`` and friends are rebuildable
projections (``AGENTS.md``, State and execution). This module reads the journal
and names every place a projection, or a receipt, says more than the journal
supports. It is the exposure half of "no service writes around the kernel":
the kernel cannot stop a caller with a reference to its state from editing it,
but it can make every such edit visible to an independent reader.
"""

from __future__ import annotations

from typing import Any

from .journal import Journal

AUTHORITY_PREDICATES = ("grant_present", "actor_matches", "type_matches",
                        "capability_matches", "scope_matches", "grant_live", "budget_available")

# Predicates a COMMITTED (or COUNTERED) receipt of each transition must carry as
# passed. A committed receipt missing one did not pass through the transition.
REQUIRED_PASSING: dict[str, tuple[str, ...]] = {
    "submit_proposal": ("proposal_complete", "authority_type_declared"),
    "admit": ("record_present", "pre_state_current", "standing_is_recorded"),
    "ratify": ("record_present", "pre_state_current", "standing_is_admitted",
               *AUTHORITY_PREDICATES),
    "attest": ("record_present", "claim_ratified", "validator_declared", "outcome_known"),
    "make_effective": ("record_present", "pre_state_current", "standing_is_ratified",
                       "no_current_counter", "no_dissent", "reproduced_on_exact_inputs"),
    "retract": ("record_present", *AUTHORITY_PREDICATES),
    "begin_run": ("plan_complete", "inputs_paired", "effect_class_admitted",
                  *AUTHORITY_PREDICATES),
    "report_run": ("run_present", "run_open", "lease_current", "lease_unexpired",
                   "worker_matches"),
    "observe_run": ("run_present", "observer_independent", "expected_predicates_observed"),
    "settle_run": ("run_present", "pre_state_current", "input_state_current", "run_open",
                   "observation_present"),
}
STANDING_OF = {"submit_proposal": "RECORDED", "admit": "ADMITTED", "ratify": "RATIFIED",
               "make_effective": "EFFECTIVE"}
MUTABLE_RECORD_FIELDS = ("standing_history", "effective", "countered_by")


def committed_receipts(journal: Journal) -> list[dict[str, Any]]:
    return [receipt for receipt in journal.bodies("RECEIPT")
            if receipt.get("outcome") in ("COMMITTED", "COUNTERED")]


def target_of(receipt: dict[str, Any]) -> str | None:
    addresses = (receipt.get("emitted_record_addresses")
                 if receipt.get("event_type") == "submit_proposal"
                 else receipt.get("input_addresses"))
    return addresses[0] if addresses else None


def audit_receipts(journal: Journal) -> list[str]:
    """A committed receipt must carry every required predicate, passed."""
    defects: list[str] = []
    for receipt in committed_receipts(journal):
        required = REQUIRED_PASSING.get(receipt.get("event_type", ""))
        if required is None:
            continue
        passed = {item.get("predicate") for item in receipt.get("precondition_results", [])
                  if item.get("result") is True}
        failed = [item.get("predicate") for item in receipt.get("precondition_results", [])
                  if item.get("result") is not True]
        missing = [name for name in required if name not in passed]
        if missing or failed:
            defects.append(f"receipt {receipt.get('receipt_id')}: {receipt.get('event_type')} "
                           f"committed without passing {sorted(set(missing + failed))}")
    return defects


def journal_standing(journal: Journal) -> tuple[dict[str, list[str]], dict[str, bool]]:
    """Rebuild each record's standing history and effectiveness from receipts alone."""
    history: dict[str, list[str]] = {}
    effective: dict[str, bool] = {}
    for receipt in committed_receipts(journal):
        target = target_of(receipt)
        if target is None:
            continue
        transition = receipt.get("event_type")
        if transition in STANDING_OF:
            history.setdefault(target, []).append(STANDING_OF[transition])
            effective[target] = transition == "make_effective"
        elif transition == "retract":
            effective[target] = False
    return history, effective


def audit_records(journal: Journal, records: dict[str, Any]) -> list[str]:
    """Every projected record must match its journaled body and journaled standing."""
    defects: list[str] = []
    journaled = {body.get("record_id"): body for body in journal.bodies("RECORD")}
    history, effective = journal_standing(journal)
    for record_id, record in records.items():
        projected = record.to_dict()
        original = journaled.get(record_id)
        if original is None:
            defects.append(f"record {record_id}: not on record")
            continue
        for name, value in original.items():
            if name not in MUTABLE_RECORD_FIELDS and projected.get(name) != value:
                defects.append(f"record {record_id}: {name} diverges from journal")
        if projected["standing_history"] != history.get(record_id, []):
            defects.append(f"record {record_id}: standing projection diverges from journal")
        if projected["effective"] != effective.get(record_id, False):
            defects.append(f"record {record_id}: effectiveness diverges from journal")
    return defects


def audit(journal: Journal, records: dict[str, Any]) -> list[str]:
    """Every visible defect: chain, receipts, committed-without-passing, projections."""
    return journal.audit() + audit_receipts(journal) + audit_records(journal, records)
