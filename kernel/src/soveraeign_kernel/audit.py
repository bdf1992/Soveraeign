"""Kernel audit: what the journal supports versus what the projections say.

The journal is the record; ``Kernel.records``, ``grants``, ``attestations``,
``observations``, ``runs``, and ``counters`` are rebuildable projections
(``AGENTS.md``, State and execution). The audit reads the journal alone and
names every place a projection, a receipt, or the journal itself says more
than the record supports. It is the exposure half of "no service writes around
the kernel": the kernel cannot stop a caller with a reference to its state from
editing it, but it can make every such edit visible to an independent reader.

Readings, each independent of the transition code:

- receipts: a committed receipt must carry every predicate its transition
  requires as passed, name journaled grants where authority was required, and
  belong to a transition this kernel realizes (this module);
- authority replay: for ``ratify``, ``retract``, and ``begin_run`` the grant
  named on the receipt is re-evaluated from its journaled body against the
  journaled record or plan and the receipt's own timestamp (this module);
- ladder and provenance: walking the journal in order, every committed receipt
  must be admitted by what precedes it, and every emitted body must be named
  by a receipt (``rebuild.py``);
- projections: every projected object must equal its journaled body, and the
  fields transitions mutate must equal what the receipts rebuild (``rebuild.py``).

What no reading can replay is the pre-state digest a transition compared
against, because the journal does not carry intermediate projections.
"""

from __future__ import annotations

from typing import Any

from . import rebuild
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
REPLAYED = ("ratify", "retract", "begin_run")


def audit_receipts(journal: Journal) -> list[str]:
    """Committed receipts: required predicates, journaled grants, realized transitions."""
    defects: list[str] = []
    grants = {body.get("grant_id") for body in journal.bodies("GRANT")}
    settlements: dict[str, int] = {}
    for receipt in journal.bodies("RECEIPT"):
        transition, receipt_id = receipt.get("event_type", ""), receipt.get("receipt_id")
        if transition == "settle_run" and receipt.get("outcome") in rebuild.SETTLED:
            run_id = rebuild.target_of(receipt) or "?"
            settlements[run_id] = settlements.get(run_id, 0) + 1
        if not rebuild.committed(receipt):
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
                               f"{named}; not on record: {unknown or 'all of them'}")
    defects.extend(f"run {run_id}: {count} settlements, expected at most one"
                   for run_id, count in settlements.items() if count > 1)
    return defects


def _requirement(transition: str, receipt: dict[str, Any], records: dict[str, Any],
                 plans: dict[str, Any]) -> dict[str, str] | None:
    """What the grant had to match, from journaled bodies: type, capability, scope."""
    if transition in ("ratify", "retract"):
        record = records.get(rebuild.target_of(receipt) or "")
        if record is None:
            return None
        return {"authority_type": record["required_authority_type"], "capability": transition,
                "scope": record["scope"]}
    emitted = receipt.get("emitted_record_addresses") or [None]
    plan = plans.get(emitted[0])  # the plan journaled for the run this receipt opened
    if plan is None:
        return None
    capabilities = plan.get("required_capabilities") or []
    return {"authority_type": "VERIFICATION",
            "capability": capabilities[0] if capabilities else "operate",
            "scope": plan.get("operation_type", "")}


def audit_authority(journal: Journal) -> list[str]:
    """Replay the authority gate for ratify, retract, and begin_run from journaled bodies."""
    defects: list[str] = []
    grants = {body["grant_id"]: body for body in journal.bodies("GRANT")}
    records = {body["record_id"]: body for body in journal.bodies("RECORD")}
    plans = {body.get("run_id"): body for body in journal.bodies("PLAN")}
    uses: dict[str, int] = {}
    for receipt in journal.bodies("RECEIPT"):
        transition, receipt_id = receipt.get("event_type"), receipt.get("receipt_id")
        if not rebuild.committed(receipt):
            continue
        for grant_id in receipt.get("authority_grant_ids", []):
            uses[grant_id] = uses.get(grant_id, 0) + 1
        if transition not in REPLAYED:
            continue
        required = _requirement(transition, receipt, records, plans)
        if required is None:
            defects.append(f"receipt {receipt_id}: {transition} has no journaled record or plan "
                           "to replay against")
            continue
        for grant_id in receipt.get("authority_grant_ids", []):
            grant = grants.get(grant_id)
            if grant is None:
                continue  # audit_receipts already names the missing body
            failed = _replay(grant, receipt, required, uses.get(grant_id, 0))
            if failed:
                defects.append(f"receipt {receipt_id}: {transition} under {grant_id} "
                               f"fails replay of {failed}")
    return defects


def _replay(grant: dict[str, Any], receipt: dict[str, Any], required: dict[str, str],
            uses: int) -> list[str]:
    try:
        at = parse_timestamp(receipt.get("created_at", ""))
        live = (grant["revoked_at"] is None
                and parse_timestamp(grant["valid_from"]) <= at
                <= parse_timestamp(grant["valid_until"]))
    except (ValueError, TypeError):
        live = False
    replay = {
        "actor_matches": grant["actor_id"] == receipt.get("actor_id"),
        "type_matches": grant["authority_type"] == required["authority_type"],
        "capability_matches": grant["capability"] == required["capability"],
        "scope_matches": scope_covers(grant["scope"], required["scope"]),
        "grant_live": live,
        "budget_available": uses <= grant["budget"],
    }
    return sorted(name for name, ok in replay.items() if not ok)


def audit(kernel: Any) -> list[str]:
    """Every visible defect: chain, receipts, authority replay, ladder, provenance, projections."""
    journal: Journal = kernel.journal
    return (journal.audit() + audit_receipts(journal) + audit_authority(journal)
            + rebuild.audit_ladder(journal) + rebuild.audit_provenance(journal)
            + rebuild.audit_projections(kernel))
