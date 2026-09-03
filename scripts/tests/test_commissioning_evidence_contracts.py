"""Positive and defeating cases for prepared commissioning evidence contracts."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402
import sov_opening_readiness  # noqa: E402


class CommissioningEvidenceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        corpus = ROOT / "conformance/fixtures/commissioning/evidence-contract-cases.json"
        cls.cases = json.loads(corpus.read_text(encoding="utf-8"))["cases"]
        cls.schemas = {
            name: json.loads((ROOT / "contracts" / name).read_text(encoding="utf-8"))
            for name in {case["schema"] for case in cls.cases}
        }
        cls.positive = {
            case["schema"]: case["record"]
            for case in cls.cases if case.get("record") is not None
        }

    def case_record(self, case: dict) -> dict:
        record = deepcopy(case.get("record") or self.positive[case["schema"]])
        if case.get("mutate_subject_kind"):
            record["subject"]["kind"] = case["mutate_subject_kind"]
        if case.get("remove"):
            record.pop(case["remove"], None)
        for key, value in (case.get("set") or {}).items():
            record[key] = value
        return record

    def test_declared_cases(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["case_id"]):
                defects = validate(self.case_record(case), self.schemas[case["schema"]])
                self.assertEqual(not defects, case["valid"], defects)

    def test_both_subjects_share_one_finding_contract(self) -> None:
        kinds = {
            self.case_record(case)["subject"]["kind"]
            for case in self.cases
            if case["case_id"] in {"finding-work-positive", "finding-participant-positive"}
        }
        self.assertEqual(kinds, {"WORK", "PARTICIPANT_IN_WORK"})

    def test_every_pinned_definition_digests_to_the_bytes_it_names(self) -> None:
        """The refusal this pin exists for: a campaign closing against a narrowed
        definition. Phase I's pins were the whole test while it was the only phase;
        phase:1-5 opened on 2026-09-03 with three pins of its own, and every one of
        them is held to the same rule."""
        phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
        by_id = {phase["phase_id"]: phase for phase in phases["phases"]}
        self.assertEqual(set(by_id), {"phase:i", "phase:1-5"})
        for phase in phases["phases"]:
            for pin in phase["definition"]:
                with self.subTest(phase=phase["phase_id"], document=pin["document"]):
                    actual = "sha256:" + sha256((ROOT / pin["document"]).read_bytes()).hexdigest()
                    self.assertEqual(actual, pin["digest"])
        self.assertEqual(by_id["phase:i"]["terminal"], "CLOSED_INCOMPLETE")
        self.assertEqual(by_id["phase:i"]["succeeded_by"], "phase:1-5")
        self.assertEqual(by_id["phase:1-5"]["terminal"], "IN_FLIGHT")
        self.assertIn("phase: phase:1-5", (ROOT / "STATUS.yaml").read_text(encoding="utf-8"))

    def test_the_profile_earns_nothing_by_being_written(self) -> None:
        """Opening the phase made this profile the definition. It did not make any
        criterion true, which is the substitution the whole record set refuses."""
        prd = (ROOT / "PRD.md").read_text(encoding="utf-8")
        spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
        self.assertIn("Phase 1.5 qualification profile", prd)
        self.assertIn("is earned merely by being written", prd)
        for criterion in ("P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4"):
            self.assertIn(criterion, prd)
            self.assertIn(criterion, spec)
        self.assertIn("candidate next Definition", prd)
        self.assertIn("gains no standing or authority", spec)
        phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
        active = next(item for item in phases["phases"] if item["phase_id"] == "phase:1-5")
        self.assertEqual(active["acceptance_status"], "NOT_EARNED")
        self.assertEqual(
            [clause["verdict"] for clause in active["exit_clauses"]],
            ["NOT_EARNED"] * 5 + ["NOT_REACHED"])

    def test_all_p15_normative_predicates_have_discriminating_fixture_pairs(self) -> None:
        report = sov_opening_readiness.commissioning_instrument(ROOT)
        self.assertEqual(report["predicates_total"], 12)
        self.assertEqual(report["predicates_covered"], 12)
        self.assertEqual(report["open"], [])
        self.assertEqual(report["defects"], [])
        self.assertTrue(report["closed"])

    def test_the_rehearsal_stops_once_the_phase_it_rehearsed_is_open(self) -> None:
        """The rehearsal graded a readiness that no longer exists to grade. With a
        phase open it reports ACTIVE_PHASE and stops, rather than re-rehearsing an
        act already performed; the instrument it checked stands on its own."""
        report = sov_opening_readiness.assess(ROOT)
        self.assertEqual(report["state"], "ACTIVE_PHASE")
        self.assertEqual(report["phase"], "phase:1-5")
        self.assertEqual(report["defects"], [])
        self.assertNotIn("checks", report)
        instrument = sov_opening_readiness.commissioning_instrument(ROOT)
        self.assertEqual(instrument["predicates_covered"], 12)
        self.assertTrue(instrument["closed"])


if __name__ == "__main__":
    unittest.main()
