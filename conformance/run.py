#!/usr/bin/env python3
"""Strategy-neutral logical oracle for the Phase-I observation contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parent
REQUIREMENTS = {f"PROD-I-{number}" for number in range(1, 10)}


def missing(mapping: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if field not in mapping or mapping[field] in (None, "", [])]


def check_i1(observed: dict[str, Any]) -> list[str]:
    proposal = observed.get("proposal") or {}
    required = ("proposal_id", "actor_id", "actor_kind", "content_address",
                "source_addresses", "cost_record", "required_authority_type",
                "scope", "standing")
    defects = [f"proposal missing {field}" for field in missing(proposal, required)]
    if observed.get("admitted") and defects:
        defects.append("incomplete proposal was admitted")
    if proposal.get("standing") not in {"RECORDED", "ADMITTED"}:
        defects.append("proposal entered with authoritative standing")
    return defects


def check_i2(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if observed.get("source_before_digest") != observed.get("source_after_digest"):
        defects.append("source changed during reading")
    recording = observed.get("recording") or {}
    required = ("source_id", "source_digest", "reader_id", "reader_version",
                "configuration_digest", "payload_digest", "fidelity")
    defects.extend(f"recording missing {field}" for field in missing(recording, required))
    if recording.get("fidelity") == "LOSSY" and not recording.get("omissions"):
        defects.append("lossy recording lacks recoverable omissions")
    return defects


def check_i3(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    human, model = observed.get("human") or {}, observed.get("model") or {}
    if not human.get("transition_contract") or human.get("transition_contract") != model.get("transition_contract"):
        defects.append("bindings do not share one transition contract")
    for name, binding in (("human", human), ("model", model)):
        if binding.get("direct_write"):
            defects.append(f"{name} binding writes authoritative state directly")
        if not binding.get("receipt_id"):
            defects.append(f"{name} binding lacks receipt")
    crossing = observed.get("crossing") or {}
    for field in ("source_id", "source_version", "projection_id", "omissions", "destination_id"):
        if field not in crossing or crossing[field] is None:
            defects.append(f"crossing missing {field}")
    return defects


def check_i4(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if not observed.get("original_record_present"):
        defects.append("retraction erased original record")
    if not observed.get("counter_record_present"):
        defects.append("retraction lacks counter-record")
    if observed.get("effect_class") not in {"RECORD_LOCAL", "RESOURCE_CONSUMPTION", "EXTERNAL_WORLD"}:
        defects.append("effect class missing or invalid")
    if observed.get("claims_world_rollback"):
        defects.append("record retraction claims world rollback")
    receipt = observed.get("receipt") or {}
    if receipt.get("outcome") != "COUNTERED" or not receipt.get("target_receipt_id"):
        defects.append("counteraction receipt incomplete")
    return defects


def check_i5(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    attempts = observed.get("attempts") or []
    if not attempts:
        return ["authority attempts missing"]
    claim_types = {attempt.get("claim_type") for attempt in attempts}
    if not {"VERIFICATION", "JUDGEMENT"}.issubset(claim_types):
        defects.append("authority scenario did not exercise both claim types")
    for index, attempt in enumerate(attempts):
        if not attempt.get("receipt_id"):
            defects.append(f"attempt {index} lacks receipt")
        authorized = all(attempt.get(key) for key in ("grant_live", "scope_matches", "budget_available"))
        if attempt.get("outcome") == "COMMITTED" and not authorized:
            defects.append(f"attempt {index} committed without live scoped budget")
        if (attempt.get("actor_kind") == "MODEL" and
                attempt.get("authority_type") == "VERIFICATION" and
                attempt.get("claim_type") == "JUDGEMENT" and
                attempt.get("outcome") != "REFUSED"):
            defects.append("machine verification authority ratified judgement")
    verification_attempts = [attempt for attempt in attempts if attempt.get("claim_type") == "VERIFICATION"]
    if not any(attempt.get("outcome") == "COMMITTED" for attempt in verification_attempts):
        defects.append("delegated verification claim did not commit")
    return defects


def check_i6(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    pending = observed.get("pending_right") or {}
    if not pending.get("persistent") or not pending.get("visible"):
        defects.append("pending judgement is hidden or ephemeral")
    if pending.get("outcome") != "UNRESOLVED" or not pending.get("receipt_id"):
        defects.append("pending judgement lacks unresolved receipt")
    if observed.get("unrelated_operation_outcome") != "COMMITTED":
        defects.append("pending judgement blocked unrelated operation")
    if not observed.get("judgement_spend_derived_from_receipts"):
        defects.append("judgement spend is not derived from receipts")
    if observed.get("invented_quota"):
        defects.append("judgement quota was invented")
    return defects


def check_i7(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    for field in ("clean_checkout", "authority_located", "conformance_executed",
                  "evidence_reconstructed", "semantic_task_observed"):
        if not observed.get(field):
            defects.append(f"qualification lacks {field}")
    if observed.get("oral_explanation_used"):
        defects.append("qualification required oral explanation")
    if not isinstance(observed.get("time_to_safe_competence_seconds"), (int, float)):
        defects.append("time to safe competence not measured")
    if observed.get("owner_acceptance") != "PENDING":
        defects.append("witness claimed owner acceptance")
    return defects


def check_i8(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    if observed.get("ratification_before") != observed.get("ratification_after"):
        defects.append("attestation changed historical ratification")
    if observed.get("validator_changed_authority"):
        defects.append("validator occupied authority slot")
    attestations = observed.get("attestations") or []
    if not attestations:
        return defects + ["attestations missing"]
    seen_inputs: set[str] = set()
    for index, attestation in enumerate(attestations):
        for field in ("validator_id", "validator_version", "input_digest", "run_id", "outcome", "evidence_addresses"):
            if field not in attestation or attestation[field] in (None, "", []):
                defects.append(f"attestation {index} missing {field}")
        digest = attestation.get("input_digest")
        if digest in seen_inputs and attestation.get("outcome") == "REPRODUCED":
            defects.append("reproduction duplicated without a distinct input state")
        if digest:
            seen_inputs.add(digest)
    if len(attestations) > 1:
        inputs = {item.get("input_digest") for item in attestations}
        if len(inputs) > 1 and all(item.get("outcome") == "REPRODUCED" for item in attestations):
            defects.append("changed inputs inherited reproduced outcome")
    return defects


def check_i9(observed: dict[str, Any]) -> list[str]:
    defects: list[str] = []
    bindings = observed.get("bindings") or []
    if len(bindings) < 2:
        defects.append("fewer than two model bindings were exercised")
    material_models = {
        (binding.get("provider_kind"), binding.get("model_id"), binding.get("runtime_id"))
        for binding in bindings
    }
    if len(material_models) < 2:
        defects.append("model bindings are not materially different")
    if bindings and not any(binding.get("owner_supplied") for binding in bindings):
        defects.append("no owner-supplied model binding was exercised")
    shared_fields = ("interface_contract_id", "operation_id", "authority_contract_id", "state_before_digest")
    for field in shared_fields:
        values = {binding.get(field) for binding in bindings}
        if len(values) != 1 or None in values or "" in values:
            defects.append(f"bindings do not share one {field}")
    required = (
        "binding_id", "adapter_id", "provider_id", "provider_kind", "model_id",
        "model_version", "runtime_id", "runtime_version", "host_id",
        "interface_contract_id", "operation_id", "authority_contract_id",
        "state_before_digest", "input_projection_id", "omissions",
        "data_boundary", "usage", "cost", "receipt_id", "result_id",
        "result_standing",
    )
    result_ids: list[str] = []
    for index, binding in enumerate(bindings):
        for field in required:
            if field not in binding or binding[field] is None or binding[field] == "":
                defects.append(f"binding {index} missing {field}")
        if binding.get("provider_kind") not in {"LOCAL", "REMOTE"}:
            defects.append(f"binding {index} has invalid provider kind")
        if binding.get("data_boundary") not in {"LOCAL_ONLY", "REDACTED_REMOTE", "REMOTE_ALLOWED"}:
            defects.append(f"binding {index} has invalid data boundary")
        if binding.get("direct_write"):
            defects.append(f"binding {index} writes authoritative state directly")
        if binding.get("result_standing") not in {"PROPOSAL", "RECORDING", "REPORT", "OBSERVATION"}:
            defects.append(f"binding {index} returned an authoritative result directly")
        if binding.get("result_id"):
            result_ids.append(binding["result_id"])
    if len(result_ids) != len(set(result_ids)):
        defects.append("different model results were silently merged")
    unavailable = observed.get("unavailable_model") or {}
    if unavailable.get("outcome") != "REFUSED" or unavailable.get("reason") != "MODEL_UNAVAILABLE":
        defects.append("unavailable model did not refuse explicitly")
    if not unavailable.get("receipt_id"):
        defects.append("unavailable model refusal lacks receipt")
    if unavailable.get("silent_fallback"):
        defects.append("unavailable model triggered silent fallback")
    if not observed.get("local_record_operable"):
        defects.append("provider loss removed local record operation")
    return defects


CHECKS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "PROD-I-1": check_i1, "PROD-I-2": check_i2, "PROD-I-3": check_i3,
    "PROD-I-4": check_i4, "PROD-I-5": check_i5, "PROD-I-6": check_i6,
    "PROD-I-7": check_i7, "PROD-I-8": check_i8, "PROD-I-9": check_i9,
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def observations_by_id(path: Path | None, cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if path is None:
        return {case["id"]: case["observed"] for case in cases}
    supplied = load_json(path)
    return {item["case_id"]: item["observed"] for item in supplied}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cases", type=Path, default=ROOT / "oracle-controls.json")
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()

    cases = load_json(args.cases)
    supplied = observations_by_id(args.observations, cases)
    results = []
    seen: dict[str, set[str]] = {requirement: set() for requirement in REQUIREMENTS}
    suite_ok = True

    for case in cases:
        case_id = case.get("id")
        requirement = case.get("requirement")
        polarity = case.get("polarity")
        expected = case.get("expected_oracle") if args.observations is None else None
        valid_polarities = {"positive", "defeating"} if args.observations is None else {"participant"}
        if requirement not in CHECKS or polarity not in valid_polarities or case_id not in supplied:
            result = {"case_id": case_id, "requirement": requirement, "verdict": "INVALID", "defects": ["invalid or missing case observation"]}
            suite_ok = False
        else:
            seen[requirement].add(polarity)
            defects = CHECKS[requirement](supplied[case_id])
            verdict = "FAIL" if defects else "PASS"
            result = {"case_id": case_id, "requirement": requirement, "polarity": polarity, "verdict": verdict, "defects": defects}
            if expected is not None and verdict != expected:
                result["oracle_mismatch"] = {"expected": expected, "actual": verdict}
                suite_ok = False
            if args.observations is not None and verdict != "PASS":
                suite_ok = False
        results.append(result)

    required_polarities = {"positive", "defeating"} if args.observations is None else {"participant"}
    missing_coverage = sorted(requirement for requirement, polarities in seen.items()
                              if polarities != required_polarities)
    if missing_coverage:
        suite_ok = False

    report = {"suite": "PASS" if suite_ok else "FAIL", "results": results,
              "missing_positive_and_defeating_coverage": missing_coverage}
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for result in results:
            print(f"{result['verdict']:7} {result.get('case_id')} {result.get('requirement')} defects={len(result.get('defects', []))}")
        print(f"SUITE   {report['suite']} cases={len(results)} coverage_gaps={len(missing_coverage)}")
    return 0 if suite_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
