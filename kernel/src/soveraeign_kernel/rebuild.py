"""Rebuild projections from the journal and check the journal against itself.

Two readings live here. The first rebuilds what each projection should say
from the receipts and bodies on record and compares. The second walks the
journal in order and asks, at every committed receipt, whether the journal up
to that point admits the transition: a rung may not be skipped, nothing becomes
effective without a reproduction on record, nothing settles without an
observation on record, and every body that a transition emits must be named by
that transition's receipt. A forged receipt that the journaled history
contradicts, or a body appended without a transition, is named here.
"""

from __future__ import annotations

from typing import Any

from .journal import Journal

STANDING_OF = {"submit_proposal": "RECORDED", "admit": "ADMITTED", "ratify": "RATIFIED",
               "make_effective": "EFFECTIVE"}
PRIOR_RUNG = {"submit_proposal": None, "admit": "RECORDED", "ratify": "ADMITTED",
              "make_effective": "RATIFIED"}
SETTLED = ("COMMITTED", "FAILED", "UNRESOLVED")
RUN_MUTABLE = ("completed_at", "outcome", "emitted_record_addresses", "report",
               "observation_ids", "begin_receipt_id")
RECORD_MUTABLE = ("standing_history", "effective", "countered_by")
# Which transition's committed receipt must name each emitted body kind.
EMITTED_BY = {"RECORD": ("submit_proposal", "record_id"),
              "ATTESTATION": ("attest", "attestation_id"),
              "RUN": ("begin_run", "run_id"),
              "OBSERVATION": ("observe_run", "observation_id"),
              "COUNTER": ("retract", "counter_record_id")}


def target_of(receipt: dict[str, Any]) -> str | None:
    addresses = (receipt.get("emitted_record_addresses")
                 if receipt.get("event_type") == "submit_proposal"
                 else receipt.get("input_addresses"))
    return addresses[0] if addresses else None


def committed(receipt: dict[str, Any]) -> bool:
    return receipt.get("outcome") in ("COMMITTED", "COUNTERED")


def rebuild_records(journal: Journal) -> tuple[dict[str, list[str]], dict[str, bool],
                                                dict[str, list[str]]]:
    """Standing history, effectiveness, and counters per record, from receipts and counters."""
    history: dict[str, list[str]] = {}
    effective: dict[str, bool] = {}
    for receipt in journal.bodies("RECEIPT"):
        target, transition = target_of(receipt), receipt.get("event_type")
        if target is None or not committed(receipt):
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


def audit_provenance(journal: Journal) -> list[str]:
    """Every emitted body must be named by a committed receipt of the transition that emits it."""
    named: dict[str, set[str]] = {}
    for receipt in journal.bodies("RECEIPT"):
        if committed(receipt):
            named.setdefault(receipt.get("event_type", ""), set()).update(
                receipt.get("emitted_record_addresses", []))
    defects: list[str] = []
    for kind, (transition, key) in EMITTED_BY.items():
        for body in journal.bodies(kind):
            if body.get(key) not in named.get(transition, set()):
                defects.append(f"{kind.lower()} {body.get(key)}: no {transition} receipt emits it")
    return defects


def audit_ladder(journal: Journal) -> list[str]:
    """Walk the journal in order; every committed receipt must be admitted by what precedes it."""
    defects: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    standing: dict[str, str | None] = {}
    attested: dict[str, list[dict[str, Any]]] = {}
    countered: set[str] = set()
    observed: set[str] = set()
    runs: set[str] = set()
    for entry in journal.entries():
        kind, body = entry.get("kind"), entry.get("body") or {}
        if kind == "RECORD":
            records[body.get("record_id")] = body
        elif kind == "ATTESTATION":
            attested.setdefault(body.get("claim_id"), []).append(body)
        elif kind == "COUNTER":
            countered.add(body.get("target_record_id"))
        elif kind == "OBSERVATION":
            observed.add(body.get("run_id"))
        elif kind == "RUN":
            runs.add(body.get("run_id"))
        elif kind == "RECEIPT":
            defects.extend(_admits(body, standing, records, attested, countered, observed, runs))
    return defects


def _admits(receipt: dict[str, Any], standing: dict[str, str | None],
            records: dict[str, dict[str, Any]], attested: dict[str, list[dict[str, Any]]],
            countered: set[str], observed: set[str], runs: set[str]) -> list[str]:
    transition, target = receipt.get("event_type"), target_of(receipt)
    receipt_id, outcome = receipt.get("receipt_id"), receipt.get("outcome")
    if not committed(receipt) and not (transition == "settle_run" and outcome in SETTLED):
        return []
    where = f"receipt {receipt_id}: {transition}"
    defects: list[str] = []
    if transition in STANDING_OF:
        if standing.get(target) != PRIOR_RUNG[transition]:
            defects.append(f"{where} over a record whose journaled standing is "
                           f"{standing.get(target)!r}, not {PRIOR_RUNG[transition]!r}")
        if transition == "make_effective":
            digests = (records.get(target) or {}).get("input_digests")
            exact = [a for a in attested.get(target, []) if a.get("input_digests") == digests]
            outcomes = {a.get("outcome") for a in exact}
            if "REPRODUCED" not in outcomes or "DISSENTED" in outcomes:
                defects.append(f"{where} without a REPRODUCED attestation over exact inputs")
            if target in countered:
                defects.append(f"{where} over a countered record")
        standing[target] = STANDING_OF[transition]
    elif transition in ("report_run", "observe_run", "settle_run") and target not in runs:
        defects.append(f"{where} over a run that is not on record")
    elif transition == "settle_run" and target not in observed:
        defects.append(f"{where} with no observation on record")
    elif transition in ("attest", "retract") and target not in records:
        defects.append(f"{where} over a record that is not on record")
    elif transition == "attest" and standing.get(target) not in ("RATIFIED", "EFFECTIVE"):
        defects.append(f"{where} over a record whose journaled standing is "
                       f"{standing.get(target)!r}, not ratified")
    return defects
