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
EXECUTOR_RELATIONS = ("EXECUTOR", "EXECUTOR_REPORT", "")
BODY_KEY = {"RECORD": "record_id", "ATTESTATION": "attestation_id", "RUN": "run_id",
            "OBSERVATION": "observation_id", "COUNTER": "counter_record_id"}
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
    seen: dict[str, dict[str, dict[str, Any]]] = {kind: {} for kind in BODY_KEY}
    standing: dict[str, str | None] = {}
    for entry in journal.entries():
        kind, body = entry.get("kind"), entry.get("body") or {}
        if kind in BODY_KEY:
            seen[kind][body.get(BODY_KEY[kind])] = body
        elif kind == "RECEIPT":
            defects.extend(_admits(body, standing, seen))
    return defects


def _emitted(receipt: dict[str, Any], kind: str, seen: dict[str, dict[str, dict[str, Any]]],
             where: str) -> tuple[list[dict[str, Any]], list[str]]:
    """The bodies a committed receipt names must be on record before it, of the right kind."""
    bodies, defects = [], []
    for address in receipt.get("emitted_record_addresses", []):
        body = seen[kind].get(address)
        if body is None:
            defects.append(f"{where} names {address} but no {kind} body is on record")
        else:
            bodies.append(body)
    if not bodies and not defects:
        defects.append(f"{where} emits no {kind} body")
    return bodies, defects


def _admits(receipt: dict[str, Any], standing: dict[str, str | None],
            seen: dict[str, dict[str, dict[str, Any]]]) -> list[str]:
    transition, target = receipt.get("event_type"), target_of(receipt)
    where = f"receipt {receipt.get('receipt_id')}: {transition}"
    settled = transition == "settle_run" and receipt.get("outcome") in SETTLED
    if not committed(receipt) and not settled:
        return []
    records, runs = seen["RECORD"], seen["RUN"]
    if transition in STANDING_OF:
        return _admits_standing(receipt, standing, seen, where)
    if transition in ("attest", "retract") and target not in records:
        return [f"{where} over a record that is not on record"]
    if transition in ("report_run", "observe_run", "settle_run") and target not in runs:
        return [f"{where} over a run that is not on record"]
    defects: list[str] = []
    if transition == "attest":
        if standing.get(target) not in ("RATIFIED", "EFFECTIVE"):
            defects.append(f"{where} over a record whose journaled standing is "
                           f"{standing.get(target)!r}, not ratified")
        bodies, named = _emitted(receipt, "ATTESTATION", seen, where)
        defects += named + [f"{where} names an attestation of another claim or no validator"
                            for a in bodies
                            if a.get("claim_id") != target or not a.get("validator_version")]
    elif transition == "retract":
        bodies, named = _emitted(receipt, "COUNTER", seen, where)
        defects += named + [f"{where} names a counter of another record"
                            for c in bodies if c.get("target_record_id") != target]
    elif transition == "begin_run":
        defects += _emitted(receipt, "RUN", seen, where)[1]
    elif transition == "report_run":
        if receipt.get("actor_id") != runs[target].get("worker_id"):
            defects.append(f"{where} by an actor who is not the run's worker")
    elif transition == "observe_run":
        bodies, named = _emitted(receipt, "OBSERVATION", seen, where)
        run = runs[target]
        defects += named + [f"{where} names an observation by the executor"
                            for o in bodies
                            if o.get("run_id") != target
                            or o.get("observer_id") in (run.get("worker_id"), run.get("actor_id"))
                            or o.get("observer_relation") in EXECUTOR_RELATIONS]
    elif settled:
        results = [item.get("result") for o in seen["OBSERVATION"].values()
                   if o.get("run_id") == target for item in o.get("predicate_results", [])]
        if not results:
            defects.append(f"{where} with no observation on record")
        else:
            derived = ("UNRESOLVED" if any(r is None for r in results)
                       else "COMMITTED" if all(results) else "FAILED")
            if receipt.get("outcome") != derived:
                defects.append(f"{where} outcome {receipt.get('outcome')} contradicts the "
                               f"observations on record ({derived})")
    return defects


def _admits_standing(receipt: dict[str, Any], standing: dict[str, str | None],
                     seen: dict[str, dict[str, dict[str, Any]]], where: str) -> list[str]:
    transition, target = receipt.get("event_type"), target_of(receipt)
    defects: list[str] = []
    if standing.get(target) != PRIOR_RUNG[transition]:
        defects.append(f"{where} over a record whose journaled standing is "
                       f"{standing.get(target)!r}, not {PRIOR_RUNG[transition]!r}")
    if transition == "submit_proposal":
        defects += _emitted(receipt, "RECORD", seen, where)[1]
    if transition == "make_effective":
        digests = (seen["RECORD"].get(target) or {}).get("input_digests")
        outcomes = {a.get("outcome") for a in seen["ATTESTATION"].values()
                    if a.get("claim_id") == target and a.get("input_digests") == digests}
        if "REPRODUCED" not in outcomes or "DISSENTED" in outcomes:
            defects.append(f"{where} without a REPRODUCED attestation over exact inputs")
        if any(c.get("target_record_id") == target for c in seen["COUNTER"].values()):
            defects.append(f"{where} over a countered record")
    standing[target] = STANDING_OF[transition]
    return defects
