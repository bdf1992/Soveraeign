#!/usr/bin/env python3
"""The transition and discovery predicates SPEC.md states below the nine requirements.

`scripts/sov_f2_gate.py` reads SPEC.md one granularity below `PROD-I-<n>`: every row of the
transition contract and every bullet under interface parity is a normative predicate that
needs a positive and a defeating fixture. Six transition rows and one parity bullet carried
neither, because no control modelled source capture, effectiveness, a run lease, an executor
report, an observer relation, settlement, or legal-operation discovery. These functions judge
observations of exactly those, so the corpus can claim them.

Same rule as `requirements.py`: each function returns the defects it can see in a submitted
observation and reads no participant verdict field. Kept apart from that module so the nine
requirement predicates stay the nine and so neither module crosses the ceiling.
"""

from __future__ import annotations

from typing import Any, Callable

#: Outcomes that settle a run. An executor report may carry none of them.
SETTLING = {"COMMITTED", "FAILED", "UNRESOLVED", "COUNTERED"}
TERMINAL_SETTLEMENTS = {"COMMITTED", "FAILED", "UNRESOLVED"}
GATES = ("capability", "budget", "input", "effect")


def missing(mapping: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    """The declared fields a mapping does not actually state; whitespace is unstated."""
    def unstated(value: Any) -> bool:
        return value in (None, "", []) or (isinstance(value, str) and not value.strip())

    return [field for field in fields if field not in mapping or unstated(mapping[field])]


def check_capture(observed: dict[str, Any]) -> list[str]:
    """`capture_source`: readable bytes under a digest they carry create an immutable source."""
    capture = observed.get("capture") or {}
    required = ("source_address", "declared_digest", "computed_digest", "receipt_id", "outcome")
    defects = [f"capture missing {field}" for field in missing(capture, required)]
    outcome = capture.get("outcome")
    if outcome == "COMMITTED":
        if capture.get("readable") is not True:
            defects.append("unreadable bytes were captured as a source")
        if capture.get("declared_digest") != capture.get("computed_digest"):
            defects.append("source captured under a digest its bytes do not carry")
        if not capture.get("source_id"):
            defects.append("committed capture created no addressable source")
    elif outcome == "REFUSED":
        if capture.get("refusal") not in {"UNREADABLE", "DIGEST_MISMATCH"}:
            defects.append("capture refused without a declared reason")
        if capture.get("source_id"):
            defects.append("refused capture still created a source")
    else:
        defects.append("capture outcome is neither COMMITTED nor REFUSED")
    return defects


def check_effective(observed: dict[str, Any]) -> list[str]:
    """`make_effective`: ratified, attestation policy met, no current counter, else refused."""
    claim = observed.get("claim") or {}
    defects = [f"claim missing {field}" for field in missing(claim, ("claim_id", "standing"))]
    policy = observed.get("attestation_policy") or {}
    attestations = observed.get("attestations") or []
    for index, attestation in enumerate(attestations):
        fields = ("attestation_id", "claim_id", "outcome", "validator_id", "inputs_digest")
        defects.extend(f"attestation {index} missing {field}"
                       for field in missing(attestation, fields))
    reproduced = [entry for entry in attestations
                  if entry.get("outcome") == "REPRODUCED"
                  and entry.get("claim_id") == claim.get("claim_id")]
    adverse = [entry.get("outcome") for entry in attestations
               if entry.get("outcome") in {"DISSENTED", "UNATTESTABLE"}]
    transition = observed.get("transition") or {}
    outcome = transition.get("outcome")
    if outcome == "EFFECTIVE":
        if claim.get("standing") != "RATIFIED":
            defects.append("claim made effective without RATIFIED standing")
        if policy.get("requires_attestation") and not reproduced:
            defects.append("attestation policy unmet yet claim made effective")
        if adverse:
            defects.append(f"claim made effective over a {adverse[0]} attestation")
        if observed.get("current_counter_present"):
            defects.append("claim made effective over a current counter")
        if missing(transition, ("event_id", "receipt_id")):
            defects.append("effective transition left no event or receipt")
    elif outcome == "REFUSED":
        if transition.get("refusal") not in {"DISSENTED", "UNATTESTABLE", "POLICY_REFUSED"}:
            defects.append("effectiveness refused without a declared reason")
        if not transition.get("receipt_id"):
            defects.append("refusal left no receipt")
        if claim.get("standing") == "EFFECTIVE":
            defects.append("refused claim reads EFFECTIVE")
    else:
        defects.append("make_effective outcome is neither EFFECTIVE nor REFUSED")
    return defects


def _begin(begin: dict[str, Any]) -> list[str]:
    """`begin_run`: a complete plan past every gate emits ATTEMPTED and leases delegation."""
    required = ("operation_plan_id", "actor_id", "input_state_digest", "event", "receipt_id")
    defects = [f"begin missing {field}" for field in missing(begin, required)]
    gates = begin.get("gates") or {}
    failed = [gate for gate in GATES if gates.get(gate) != "PASS"]
    if begin.get("event") == "ATTEMPTED":
        if failed:
            defects.append(f"run began past a failed gate: {', '.join(failed)}")
        lease = begin.get("lease") or {}
        if begin.get("delegated") and missing(lease, ("holder_id", "fence", "expires_at")):
            defects.append("delegated run began without a complete lease")
    elif begin.get("event") == "REFUSED":
        if begin.get("refusal") not in {"AUTHORITY_REFUSED", "EFFECT_CLASS_REFUSED",
                                        "MISSING_PRECONDITION"}:
            defects.append("begin refused without a declared reason")
    else:
        defects.append("begin event is neither ATTEMPTED nor REFUSED")
    return defects


def _report(begin: dict[str, Any], report: dict[str, Any]) -> list[str]:
    """`report_run`: stored under the current lease and fence; it settles nothing."""
    required = ("worker_id", "lease_fence", "reported_at", "output_record_addresses", "standing")
    defects = [f"report missing {field}" for field in missing(report, required)]
    lease = begin.get("lease") or {}
    if lease:
        if (report.get("worker_id") != lease.get("holder_id")
                or report.get("lease_fence") != lease.get("fence")):
            defects.append("report accepted under a stale lease")
        reported_at, expires_at = report.get("reported_at"), lease.get("expires_at")
        if isinstance(reported_at, (int, float)) and isinstance(expires_at, (int, float)):
            if reported_at > expires_at:
                defects.append("report accepted after the lease expired")
    if report.get("standing") != "REPORT":
        defects.append("executor output entered with a standing other than REPORT")
    if report.get("settled") or report.get("outcome") in SETTLING:
        defects.append("executor report settled the run")
    return defects


def _observation(begin: dict[str, Any], report: dict[str, Any],
                 observation: dict[str, Any]) -> list[str]:
    """`observe_run`: an inferred independent observer read the outputs against prior predicates."""
    required = ("observation_id", "observer_id", "observed_state_addresses",
                "observed_state_digests", "predicate_results", "predicates_declared_at",
                "observed_at", "standing")
    defects = [f"observation missing {field}" for field in missing(observation, required)]
    executor = begin.get("actor_id") or report.get("worker_id")
    if observation.get("observer_id") == executor:
        defects.append("executor observed its own run")
    inference = observation.get("relation_inference") or {}
    if inference.get("outcome") != "INDEPENDENT":
        defects.append(f"observation admitted without an INDEPENDENT inference "
                       f"({inference.get('outcome') or 'none'})")
    if inference.get("edges_found"):
        defects.append("observation admitted with a direct edge to the run")
    if inference.get("record_completeness") != "COMPLETE":
        defects.append("independence read over an incomplete record")
    declared = observation.get("predicates_declared_at")
    observed_at = observation.get("observed_at")
    if isinstance(declared, (int, float)) and isinstance(observed_at, (int, float)):
        if declared >= observed_at:
            defects.append("predicates declared after the looking")
    addresses = observation.get("observed_state_addresses") or []
    outputs = report.get("output_record_addresses") or []
    if not set(addresses) & set(outputs):
        defects.append("observer read none of the run's durable outputs")
    if len(addresses) != len(observation.get("observed_state_digests") or []):
        defects.append("observed digests do not align with observed addresses")
    if observation.get("standing") != "OBSERVATION":
        defects.append("observation entered with a standing other than OBSERVATION")
    return defects


def _settlement(observed: dict[str, Any]) -> list[str]:
    """`settle_run`: current input state plus a satisfactory observation, by someone else."""
    begin = observed.get("begin") or {}
    observation = observed.get("observation") or {}
    settlement = observed.get("settlement") or {}
    required = ("input_state_digest", "current_state_digest", "observation_id", "outcome",
                "receipt_id", "settled_by")
    defects = [f"settlement missing {field}" for field in missing(settlement, required)]
    if settlement.get("observation_id") != observation.get("observation_id"):
        defects.append("settlement cites no observation of this run")
    if settlement.get("input_state_digest") != settlement.get("current_state_digest"):
        defects.append("run settled against a stale state")
    if settlement.get("input_state_digest") != begin.get("input_state_digest"):
        defects.append("settlement input state is not the state the run began on")
    if settlement.get("outcome") not in TERMINAL_SETTLEMENTS:
        defects.append("settlement outcome is not a terminal receipt outcome")
    results = observation.get("predicate_results") or {}
    if settlement.get("outcome") == "COMMITTED" and any(v is not True for v in results.values()):
        defects.append("run committed against a failed predicate")
    if settlement.get("settled_by") in {begin.get("actor_id"), observation.get("observer_id")}:
        defects.append("a participant in the run settled it")
    return defects


def check_run(observed: dict[str, Any]) -> list[str]:
    """One run through `begin_run`, `report_run`, `observe_run`, and `settle_run`."""
    begin = observed.get("begin") or {}
    defects = _begin(begin)
    if begin.get("event") != "ATTEMPTED":
        return defects
    report = observed.get("report") or {}
    defects.extend(_report(begin, report))
    defects.extend(_observation(begin, report, observed.get("observation") or {}))
    defects.extend(_settlement(observed))
    return defects


def check_discovery(observed: dict[str, Any]) -> list[str]:
    """`PARITY-1`: both bindings discover the same legal operations and required inputs."""
    defects: list[str] = []
    interface = observed.get("interface_id")
    if not interface:
        defects.append("discovery names no interface")
    discovered: dict[str, dict[str, set[str]]] = {}
    for name in ("human", "model"):
        binding = observed.get(name) or {}
        for field in missing(binding, ("binding_id", "discovery_receipt_id", "operations")):
            defects.append(f"{name} binding missing {field}")
        if binding.get("interface_id") != interface:
            defects.append(f"{name} binding discovered from a different interface")
        if binding.get("direct_write"):
            defects.append(f"{name} binding writes authoritative state directly")
        operations: dict[str, set[str]] = {}
        for entry in binding.get("operations") or []:
            if not entry.get("operation_id") or not isinstance(entry.get("required_inputs"), list):
                defects.append(f"{name} binding discovered an operation without id or inputs")
                continue
            operations[entry["operation_id"]] = set(entry["required_inputs"])
        discovered[name] = operations
    human, model = discovered.get("human", {}), discovered.get("model", {})
    for operation in sorted(set(human) ^ set(model)):
        defects.append(f"bindings do not discover the same legal operations: {operation}")
    for operation in sorted(set(human) & set(model)):
        if human[operation] != model[operation]:
            defects.append(f"bindings do not discover the same required inputs: {operation}")
    return defects


CHECKS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "SPEC-CAPTURE": check_capture,
    "SPEC-EFFECTIVE": check_effective,
    "SPEC-RUN": check_run,
    "SPEC-DISCOVERY": check_discovery,
}
