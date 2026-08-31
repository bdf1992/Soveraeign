"""Execute the principled-deviation contract and its defeating worlds.

The oracle reads governing context, append-only records, receipts, and witness
facts from fixtures. It imports no participant implementation. Passing establishes
BUILT evidence for decision 0101; it does not accept or ratify that policy.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402

SCHEMA = json.loads(
    (ROOT / "contracts" / "principled-deviation.schema.json").read_text("utf-8")
)
RAW_CASES = json.loads(
    (
        ROOT
        / "conformance"
        / "fixtures"
        / "deviation"
        / "principled-deviation-cases.json"
    ).read_text("utf-8")
)


def set_path(target: Any, dotted_path: str, value: Any) -> None:
    """Apply one fixture override through dot-separated mapping keys and list indexes."""
    parts = dotted_path.split(".")
    node = target
    for part in parts[:-1]:
        node = node[int(part)] if isinstance(node, list) else node[part]
    final = parts[-1]
    if isinstance(node, list):
        node[int(final)] = value
    else:
        node[final] = value


def materialize(raw_cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Resolve defeating fixtures from named positive templates without hiding deltas."""
    templates = {case["id"]: case for case in raw_cases if "template" not in case}
    cases: list[dict[str, Any]] = []
    for raw in raw_cases:
        if "template" not in raw:
            cases.append(deepcopy(raw))
            continue
        case = deepcopy(templates[raw["template"]])
        case.update(
            {
                "id": raw["id"],
                "polarity": raw["polarity"],
                "defeats": raw["defeats"],
                "expected_admissibility": raw["expected_admissibility"],
            }
        )
        for path, value in raw["overrides"].items():
            set_path(case, path, deepcopy(value))
        cases.append(case)
    return cases


CASES = materialize(RAW_CASES)


def instant(value: str) -> datetime:
    """Parse the fixture's RFC 3339 instant after schema validation."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def deviation_defects(case: dict[str, Any]) -> list[str]:
    """Grade authority, source ownership, truthful ordering, evidence, and learning."""
    defects: list[str] = []
    records = case.get("records", [])
    for index, record in enumerate(records):
        defects.extend(f"record {index}: {defect}" for defect in validate(record, SCHEMA))

    intents = [record for record in records if record.get("record_kind") == "INTENT"]
    outcomes = [record for record in records if record.get("record_kind") == "OUTCOME"]
    if len(intents) != 1 or len(outcomes) != 1:
        defects.append("one INTENT and one OUTCOME record are required")
        return defects

    intent, outcome = intents[0], outcomes[0]
    source = case["governing_rule"]
    authority = case["authority"]
    receipt = case["action_receipt"]

    if not authority["authorized"]:
        defects.append("deviation does not supply authority")
    if not authority["invariants_preserved"]:
        defects.append("invariants were not preserved")
    if source["rule_class"] == "INVARIANT":
        defects.append("an invariant has no deviation route")
    for field in (
        "rule_ref",
        "rule_revision",
        "rule_class",
        "governing_intent_ref",
        "governing_intent_revision",
    ):
        if intent[field] != source[field]:
            defects.append(f"{field} does not match the governing source")
    if case["governing_conflict"]:
        defects.append("material governing conflict requires escalation")

    action_at = instant(receipt["recorded_at"])
    intent_at = instant(intent["recorded_at"])
    outcome_at = instant(outcome["recorded_at"])
    if intent["timing"] == "BEFORE_ACTION":
        if intent_at > action_at:
            defects.append("post-action intent claims BEFORE_ACTION")
        if "action_receipt_ref" in intent:
            defects.append("pre-action intent cites a receipt that did not yet exist")
    else:
        if intent_at <= action_at:
            defects.append("AFTER_ACTION intent does not follow the action")
        if intent.get("action_receipt_ref") != receipt["receipt_ref"]:
            defects.append("AFTER_ACTION intent does not cite the action receipt")
    if outcome_at <= max(action_at, intent_at):
        defects.append("outcome does not follow both intent record and action")
    if outcome["deviation_id"] != intent["deviation_id"]:
        defects.append("append-only records do not share one deviation identity")
    if outcome["intent_record_ref"] != intent["record_id"]:
        defects.append("outcome does not cite its intent record")
    if outcome["action_receipt_ref"] != receipt["receipt_ref"]:
        defects.append("outcome does not cite the action receipt")

    witness = case["witness"]
    if outcome.get("witness_ref") != witness["witness_ref"]:
        defects.append("outcome does not cite the declared witness")
    if witness["evidence_kind"] == "EXPERIENCE" or not witness["independent"]:
        defects.append("experience evidence cannot satisfy independent witness")
    extra = case["overperformance"]
    if extra["present"] and not extra["separable"]:
        defects.append("extra value cannot be rejected without losing requested value")
    if case["policy_effect"] == "RULE_CHANGED":
        defects.append("deviation evidence cannot change its governing rule")
    if outcome["disposition"] == "RULE_CHANGE_CANDIDATE":
        if not outcome.get("policy_candidate_ref"):
            defects.append("rule-change candidate has no candidate reference")
    elif outcome.get("policy_candidate_ref"):
        defects.append("non-candidate disposition carries a policy candidate")

    # These fixtures exercise the deviation route. Ordinary compliance never
    # bypasses the authority and invariant perimeter shared by both routes.
    return defects


class PrincipledDeviationFixtures(unittest.TestCase):
    def test_every_case_matches_its_declared_admissibility(self) -> None:
        for case in CASES:
            with self.subTest(case=case["id"]):
                defects = deviation_defects(case)
                if case["expected_admissibility"]:
                    self.assertEqual(defects, [], case["id"])
                else:
                    self.assertNotEqual(defects, [], case["id"])

    def test_fixture_hygiene(self) -> None:
        ids = [case["id"] for case in RAW_CASES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate fixture id")
        self.assertEqual(
            {case["polarity"] for case in RAW_CASES}, {"positive", "defeating"}
        )
        covered = " ".join(case.get("defeats", "") for case in RAW_CASES)
        for requirement in ("PD-1", "PD-2", "PD-3", "PD-4", "PD-5", "PD-6", "PD-7", "PD-8"):
            self.assertIn(requirement, covered, f"{requirement} has no defeating case")

    def test_schema_refuses_mutating_intent_into_outcome(self) -> None:
        positive = next(case for case in CASES if case["id"] == "PD-POS-GOVERNED")
        intent = deepcopy(positive["records"][0])
        intent["observed_outcome"] = "Retrospectively filled in."
        self.assertNotEqual(validate(intent, SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
