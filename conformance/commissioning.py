"""Independent predicates for the prepared Phase 1.5 commissioning profile.

The checks grade observation-shaped evidence and import no participant code.
They establish whether the qualification instrument can distinguish the claim
from its defeating case; they do not establish that the product currently
satisfies the claim.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable
import json


PREDICATES = {
    "P15-Q1.1", "P15-Q1.2", "P15-Q1.3",
    "P15-Q2.1", "P15-Q2.2", "P15-Q2.3", "P15-Q2.4",
    "P15-Q3.1", "P15-Q3.2",
    "P15-Q4.1", "P15-Q4.2", "P15-Q4.3",
}


def _missing(mapping: dict[str, Any], fields: tuple[str, ...]) -> list[str]:
    return [field for field in fields if mapping.get(field) in (None, "", [])]


def check_q11(observed: dict[str, Any]) -> list[str]:
    required = ("principal_id", "session_id", "phase_state", "work_address",
                "capability", "required_authority", "effect_envelope",
                "governance_context", "record_projection_id")
    defects = [f"fresh context missing {field}" for field in _missing(observed, required)]
    if observed.get("oral_history_used") is not False:
        defects.append("fresh participation required oral history")
    return defects


def check_q12(observed: dict[str, Any]) -> list[str]:
    work = observed.get("work") or {}
    required = ("address", "custody_or_lease", "closure_condition",
                "defeating_condition", "cleanup_obligations")
    defects = [f"durable work missing {field}" for field in _missing(work, required)]
    if observed.get("survives_session") is not True:
        defects.append("work does not survive the carrying session")
    return defects


def check_q13(observed: dict[str, Any]) -> list[str]:
    defects = []
    identities = observed.get("identities") or {}
    for field in ("principal_id", "session_id", "grant_id", "interface_binding_id"):
        if identities.get(field) in (None, ""):
            defects.append(f"identity separation missing {field}")
    if len({str(value) for value in identities.values() if value not in (None, "")}) != len(identities):
        defects.append("principal, session, grant, and interface binding collapsed")
    if observed.get("cross_principal_session_mismatch") != "REFUSED":
        defects.append("cross-principal/session mismatch did not refuse")
    return defects


def check_q21(observed: dict[str, Any]) -> list[str]:
    defects = []
    if not observed.get("consequential_event_addresses"):
        defects.append("consequential history has no Record addresses")
    if observed.get("record_reconstructable") is not True:
        defects.append("operational history is not reconstructable from Record")
    if observed.get("private_state_authoritative") is not False:
        defects.append("participant-private state became authoritative history")
    return defects


def check_q22(observed: dict[str, Any]) -> list[str]:
    projection = observed.get("projection") or {}
    required = ("projection_id", "subject_addresses", "recipient_relation", "as_of",
                "included_records", "omissions", "projection_digest")
    defects = [f"RecordProjection missing {field}" for field in _missing(projection, required)]
    if projection.get("authority_effect") != "NONE":
        defects.append("RecordProjection changed authority")
    if observed.get("reconstructable") is not True:
        defects.append("RecordProjection cannot be reconstructed")
    return defects


def check_q23(observed: dict[str, Any]) -> list[str]:
    findings = observed.get("findings") or []
    kinds = {finding.get("subject_kind") for finding in findings}
    defects = []
    if kinds != {"WORK", "PARTICIPANT_IN_WORK"}:
        defects.append("work and participant-in-work are not separate Finding subjects")
    allowed = set(observed.get("projection_evidence_addresses") or [])
    for index, finding in enumerate(findings):
        if not finding.get("evaluator") or not finding.get("scope"):
            defects.append(f"finding {index} lacks evaluator or scope")
        cited = set(finding.get("evidence_addresses") or [])
        if not cited or not cited.issubset(allowed):
            defects.append(f"finding {index} cites evidence outside its RecordProjection")
    return defects


def check_q24(observed: dict[str, Any]) -> list[str]:
    defects = []
    if observed.get("projections_frozen_before_sharing") is not True:
        defects.append("independent evaluative projections were contaminated before freeze")
    comparison = observed.get("comparison") or {}
    for field in ("input_finding_ids", "citations_preserved", "counterevidence_preserved",
                  "dissent_preserved", "classification"):
        if comparison.get(field) in (None, "", []):
            defects.append(f"comparison missing {field}")
    if comparison.get("settled_missing_evidence_by_preference") is not False:
        defects.append("comparison settled missing evidence by preference")
    return defects


def check_q31(observed: dict[str, Any]) -> list[str]:
    defects = []
    if observed.get("independent_observation_present") is not True:
        defects.append("settlement lacks required independent observation")
    if observed.get("settled_against_current_state") is not True:
        defects.append("settlement was not against current state")
    if observed.get("temporary_inventory_remaining") not in ([], None):
        defects.append("closure left temporary coordination inventory")
    if observed.get("closure_receipt") in (None, ""):
        defects.append("closure lacks receipt")
    return defects


def check_q32(observed: dict[str, Any]) -> list[str]:
    required = ("result_address", "standing", "basis", "receipt_addresses", "capability")
    defects = [f"fresh reuse missing {field}" for field in _missing(observed, required)]
    if observed.get("fresh_participant_used_result") is not True:
        defects.append("fresh participant did not use the accepted result")
    if observed.get("oral_history_used") is not False:
        defects.append("reuse required builder or prior-session oral history")
    return defects


def check_q41(observed: dict[str, Any]) -> list[str]:
    candidate = observed.get("candidate") or {}
    source = set(candidate.get("source_addresses") or [])
    basis = set(observed.get("settled_evidence_addresses") or [])
    defects = []
    if not candidate.get("proposal_id") or not source:
        defects.append("candidate Definition lacks proposal identity or cited sources")
    if not basis or not basis.issubset(source):
        defects.append("candidate Definition did not preserve its settled evidence basis")
    return defects


def check_q42(observed: dict[str, Any]) -> list[str]:
    candidate = observed.get("candidate") or {}
    defects = []
    if candidate.get("standing") not in {"RECORDED", "PROPOSED"}:
        defects.append("candidate acquired standing from experience")
    if candidate.get("authority_effect") != "NONE":
        defects.append("candidate acquired authority from evidence")
    if observed.get("automatic_policy_change") is not False:
        defects.append("successful experience automatically changed policy")
    if observed.get("automatic_phase_transition") is not False:
        defects.append("successful experience automatically changed phase")
    return defects


def check_q43(observed: dict[str, Any]) -> list[str]:
    primitives = set(observed.get("generic_primitives") or [])
    required = {"identity", "session", "authority", "work", "custody", "record_projection",
                "observation", "finding", "settlement", "discovery"}
    defects = []
    if not required.issubset(primitives):
        defects.append("institution-neutral composition lacks governed primitives")
    if observed.get("fixed_role_names_required") is not False:
        defects.append("composition depends on fixed proving-role names")
    if observed.get("alternate_institution_composes") is not True:
        defects.append("alternate institution cannot compose the same primitives")
    return defects


CHECKS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "P15-Q1.1": check_q11, "P15-Q1.2": check_q12, "P15-Q1.3": check_q13,
    "P15-Q2.1": check_q21, "P15-Q2.2": check_q22, "P15-Q2.3": check_q23,
    "P15-Q2.4": check_q24, "P15-Q3.1": check_q31, "P15-Q3.2": check_q32,
    "P15-Q4.1": check_q41, "P15-Q4.2": check_q42, "P15-Q4.3": check_q43,
}


def evaluate(predicate_id: str, observed: dict[str, Any]) -> list[str]:
    check = CHECKS.get(predicate_id)
    return [f"unknown commissioning predicate {predicate_id}"] if check is None else check(observed)


FIXTURES = "conformance/fixtures/commissioning/qualification-cases.json"
REQUIRED_POLARITIES = frozenset({"positive", "defeating"})


def _set_path(record: object, dotted: str, value: Any) -> None:
    """Apply one fixture mutation through dict keys and list indices."""
    parts = dotted.split(".")
    current = record
    for part in parts[:-1]:
        current = current[int(part)] if isinstance(current, list) else current[part]
    leaf = parts[-1]
    if isinstance(current, list):
        current[int(leaf)] = value
    else:
        current[leaf] = value


def run_cases(root: Path, stated: set[str] | None = None) -> dict[str, Any]:
    """Run the declared corpus and report which predicates discriminate both ways.

    The reading is about the instrument, not the product: a covered predicate
    means the check separates its claim from its defeating case, never that the
    node currently satisfies the claim.

    `stated` is the predicate set the specification states, when the caller
    knows it. A case naming a predicate outside that set is refused by name
    rather than surfacing as a discrimination failure, which would attribute
    the defect to the fixture instead of to the predicate set.
    """
    fixture_path = root / FIXTURES
    if not fixture_path.is_file():
        return {"coverage": {}, "defects": ["qualification fixture corpus missing"], "cases": 0}
    document = json.loads(fixture_path.read_text(encoding="utf-8"))
    templates = document.get("templates") or {}
    cases = document.get("cases") or []
    coverage: dict[str, set[str]] = {}
    defects: list[str] = []

    for case in cases:
        predicate = str(case.get("predicate") or "")
        polarity = case.get("polarity")
        case_id = str(case.get("case_id") or predicate or "unnamed")
        if stated is not None and predicate not in stated:
            defects.append(f"{case_id}: predicate absent from SPEC.md")
            continue
        if polarity not in REQUIRED_POLARITIES:
            defects.append(f"{case_id}: invalid polarity {polarity}")
            continue
        template = templates.get(predicate)
        if not isinstance(template, dict):
            defects.append(f"{case_id}: no observation template")
            continue
        observation = deepcopy(template)
        broken = False
        for dotted, value in (case.get("set") or {}).items():
            try:
                _set_path(observation, str(dotted), value)
            except (KeyError, IndexError, TypeError, ValueError):
                defects.append(f"{case_id}: mutation path {dotted} does not resolve")
                broken = True
                break
        if broken:
            continue
        seen = evaluate(predicate, observation)
        discriminates = (not seen) if polarity == "positive" else bool(seen)
        if not discriminates:
            defects.append(
                f"{case_id}: {polarity} case did not discriminate "
                f"({'; '.join(seen) or 'no defect'})")
            continue
        coverage.setdefault(predicate, set()).add(str(polarity))

    return {"coverage": coverage, "defects": defects, "cases": len(cases)}


def main() -> int:
    """Print whether every declared predicate discriminates its defeating case."""
    root = Path(__file__).resolve().parents[1]
    reading = run_cases(root)
    coverage = reading["coverage"]
    uncovered = sorted(
        predicate for predicate in PREDICATES
        if REQUIRED_POLARITIES - coverage.get(predicate, set()))

    print(f"commissioning instrument: {len(PREDICATES) - len(uncovered)}/{len(PREDICATES)}"
          f" predicate(s) discriminating over {reading['cases']} case(s)")
    for predicate in sorted(PREDICATES):
        have = coverage.get(predicate, set())
        missing = sorted(REQUIRED_POLARITIES - have)
        state = "both polarities" if not missing else "MISSING " + ", ".join(missing)
        print(f"  {predicate:<9} {state}")
    for defect in reading["defects"]:
        print(f"  DEFECT  {defect}")
    if reading["defects"] or uncovered:
        return 1
    print("PASS: the instrument separates every stated predicate from its defeating case")
    print("      discrimination is not evidence that the node satisfies any predicate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
