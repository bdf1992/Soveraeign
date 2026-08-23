"""Kernel audit: what the journal supports versus what the projections say.

The journal is the record; ``Kernel.records``, ``grants``, ``attestations``,
``observations``, ``runs``, and ``counters`` are rebuildable projections
(``AGENTS.md``, State and execution). This module reads the journal and names
every place a projection, or a receipt, says more than the journal supports. It
is the exposure half of "no service writes around the kernel": the kernel cannot
stop a caller with a reference to its state from editing it, but it can make
every such edit visible to an independent reader.

Three readings, each independent of the transition code:

- receipts: a committed receipt must carry every predicate its transition
  requires as passed, name journaled grants where authority was required, and
  belong to a transition this kernel realizes;
- authority replay: for ``ratify`` and ``retract`` the grant named on the
  receipt is re-evaluated from its journaled body against the journaled record
  and the receipt's own timestamp;
- projections: every projected object must equal its journaled body, and the
  fields transitions mutate must equal what the receipts on record rebuild.
"""

from __future__ import annotations

from typing import Any

from .authority import parse_timestamp, scope_covers
from .journal import Journal
from .records import KERNEL_TRANSITIONS

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
CAPABILITY_OF = {"ratify": "ratify", "retract": "retract"}
SETTLED = ("COMMITTED", "FAILED", "UNRESOLVED")
RUN_MUTABLE = ("completed_at", "outcome", "emitted_record_addresses", "report",
               "observation_ids", "begin_receipt_id")
RECORD_MUTABLE = ("standing_history", "effective", "countered_by")


def committed_receipts(journal: Journal) -> list[dict[str, Any]]:
    return [receipt for receipt in journal.bodies("RECEIPT")
            if receipt.get("outcome") in ("COMMITTED", "COUNTERED")]


def target_of(receipt: dict[str, Any]) -> str | None:
    addresses = (receipt.get("emitted_record_addresses")
                 if receipt.get("event_type") == "submit_proposal"
                 else receipt.get("input_addresses"))
    return addresses[0] if addresses else None


def audit_receipts(journal: Journal) -> list[str]:
    """Committed receipts: required predicates, journaled grants, realized transitions."""
    defects: list[str] = []
    grants = {body.get("grant_id") for body in journal.bodies("GRANT")}
    settlements: dict[str, int] = {}
    for receipt in journal.bodies("RECEIPT"):
        transition, receipt_id = receipt.get("event_type", ""), receipt.get("receipt_id")
        if transition == "settle_run" and receipt.get("outcome") in SETTLED:
            run_id = target_of(receipt) or "?"
            settlements[run_id] = settlements.get(run_id, 0) + 1
        if receipt.get("outcome") not in ("COMMITTED", "COUNTERED"):
            continue
        required = REQUIRED_PASSING.get(transition)
        if transition not in KERNEL_TRANSITIONS or required is None:
            defects.append(f"receipt {receipt_id}: {transition!r} is not realized by this kernel")
            continue
        results = receipt.get("precondition_results", [])
        passed = {item.get("predicate") for item in results if item.get("result") is True}
        failed = [item.get("predicate") for item in results if item.get("result") is not True]
        missing = [name for name in required if name not in passed]
        if transition == "retract" and receipt.get("effect_class") != "RECORD_LOCAL":
            missing += [] if "consumption_named" in passed else ["consumption_named"]
        if missing or failed:
            defects.append(f"receipt {receipt_id}: {transition} committed without passing "
                           f"{sorted(set(missing + failed))}")
        if "grant_present" in required:
            named = receipt.get("authority_grant_ids") or []
            unknown = [grant_id for grant_id in named if grant_id not in grants]
            if not named or unknown:
                defects.append(f"receipt {receipt_id}: {transition} committed under grants "
                               f"{named} of which {unknown or 'none'} are on record")
    defects.extend(f"run {run_id}: {count} settlements, expected at most one"
                   for run_id, count in settlements.items() if count > 1)
    return defects


def audit_authority(journal: Journal) -> list[str]:
    """Replay the authority gate for ratify and retract from journaled bodies alone."""
    defects: list[str] = []
    grants = {body["grant_id"]: body for body in journal.bodies("GRANT")}
    records = {body["record_id"]: body for body in journal.bodies("RECORD")}
    uses: dict[str, int] = {}
    for receipt in journal.bodies("RECEIPT"):
        transition = receipt.get("event_type")
        committed = receipt.get("outcome") in ("COMMITTED", "COUNTERED")
        if committed:
            for grant_id in receipt.get("authority_grant_ids", []):
                uses[grant_id] = uses.get(grant_id, 0) + 1
        if not committed or transition not in CAPABILITY_OF:
            continue
        record = records.get(target_of(receipt) or "")
        receipt_id, created = receipt.get("receipt_id"), receipt.get("created_at", "")
        for grant_id in receipt.get("authority_grant_ids", []):
            grant = grants.get(grant_id)
            if grant is None or record is None:
                continue  # audit_receipts already names the missing body
            try:
                at = parse_timestamp(created)
                live = (grant["revoked_at"] is None
                        and parse_timestamp(grant["valid_from"]) <= at
                        <= parse_timestamp(grant["valid_until"]))
            except (ValueError, TypeError):
                live = False
            replay = {
                "actor_matches": grant["actor_id"] == receipt.get("actor_id"),
                "type_matches": grant["authority_type"] == record["required_authority_type"],
                "capability_matches": grant["capability"] == CAPABILITY_OF[transition],
                "scope_matches": scope_covers(grant["scope"], record["scope"]),
                "grant_live": live,
                "budget_available": uses.get(grant_id, 0) <= grant["budget"],
            }
            failed = sorted(name for name, ok in replay.items() if not ok)
            if failed:
                defects.append(f"receipt {receipt_id}: {transition} under {grant_id} "
                               f"fails replay of {failed}")
    return defects


def rebuild_records(journal: Journal) -> tuple[dict[str, list[str]], dict[str, bool],
                                                dict[str, list[str]]]:
    """Standing history, effectiveness, and counters per record, from receipts and counters."""
    history: dict[str, list[str]] = {}
    effective: dict[str, bool] = {}
    for receipt in committed_receipts(journal):
        target, transition = target_of(receipt), receipt.get("event_type")
        if target is None:
            continue
        if transition in STANDING_OF:
            history.setdefault(target, []).append(STANDING_OF[transition])
            effective[target] = transition == "make_effective"
        elif transition == "retract":
            effective[target] = False
    countered: dict[str, list[str]] = {}
    for counter in journal.bodies("COUNTER"):
        countered.setdefault(counter.get("target_record_id"), []).append(
            counter.get("counter_record_id"))
    return history, effective, countered


def rebuild_runs(journal: Journal) -> tuple[dict[str, str], dict[str, list[str]]]:
    """Run outcome and observation ids per run, from receipts and observations."""
    outcome: dict[str, str] = {}
    for receipt in journal.bodies("RECEIPT"):
        if receipt.get("event_type") == "settle_run" and receipt.get("outcome") in SETTLED:
            outcome[target_of(receipt) or "?"] = receipt["outcome"]
    observations: dict[str, list[str]] = {}
    for body in journal.bodies("OBSERVATION"):
        observations.setdefault(body.get("run_id"), []).append(body.get("observation_id"))
    return outcome, observations


def audit_projection(name: str, projected: dict[str, Any], journaled: dict[str, dict[str, Any]],
                     mutable: tuple[str, ...] = ()) -> list[str]:
    """Every projected object must match its journaled body on every immutable field."""
    defects: list[str] = []
    for key, item in projected.items():
        body = journaled.get(key)
        if body is None:
            defects.append(f"{name} {key}: not on record")
            continue
        current = item.to_dict()
        for field, value in body.items():
            if field not in mutable and current.get(field) != value:
                defects.append(f"{name} {key}: {field} diverges from journal")
    return defects


def audit_projections(kernel: Any) -> list[str]:
    journal: Journal = kernel.journal
    by = lambda kind, key: {body.get(key): body for body in journal.bodies(kind)}  # noqa: E731
    defects = audit_projection("grant", kernel.grants, by("GRANT", "grant_id"))
    defects += audit_projection("attestation", kernel.attestations,
                                by("ATTESTATION", "attestation_id"))
    defects += audit_projection("observation", kernel.observations,
                                by("OBSERVATION", "observation_id"))
    defects += audit_projection("counter", kernel.counters, by("COUNTER", "counter_record_id"))
    defects += audit_projection("record", kernel.records, by("RECORD", "record_id"),
                                RECORD_MUTABLE)
    defects += audit_projection("run", kernel.runs, by("RUN", "run_id"), RUN_MUTABLE)
    history, effective, countered = rebuild_records(journal)
    for record_id, record in kernel.records.items():
        if record.standing_history != history.get(record_id, []):
            defects.append(f"record {record_id}: standing projection diverges from journal")
        if record.effective != effective.get(record_id, False):
            defects.append(f"record {record_id}: effectiveness diverges from journal")
        if record.countered_by != countered.get(record_id, []):
            defects.append(f"record {record_id}: counters diverge from journal")
    outcome, observations = rebuild_runs(journal)
    for run_id, run in kernel.runs.items():
        if run.outcome != outcome.get(run_id, "ATTEMPTED"):
            defects.append(f"run {run_id}: outcome diverges from journal")
        if run.observation_ids != observations.get(run_id, []):
            defects.append(f"run {run_id}: observations diverge from journal")
    return defects


def audit(kernel: Any) -> list[str]:
    """Every visible defect: chain, receipts, authority replay, projections."""
    journal: Journal = kernel.journal
    return (journal.audit() + audit_receipts(journal) + audit_authority(journal)
            + audit_projections(kernel))
