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
from sovsession import phase_context  # noqa: E402
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

    def test_phase_i_spec_archive_is_exact(self) -> None:
        """Permanent: the closed Phase-I pin never moves, no matter what opens after it."""
        phases = json.loads((ROOT / "contracts/phases.json").read_text(encoding="utf-8"))
        phase_i = next(item for item in phases["phases"] if item["phase_id"] == "phase:i")
        pin = next(item for item in phase_i["definition"]
                   if item["document"] == "archives/SPEC-PHASE-I-TERMINAL.txt")
        actual = "sha256:" + sha256((ROOT / pin["document"]).read_bytes()).hexdigest()
        self.assertEqual(actual, pin["digest"])
        self.assertEqual(phase_i["terminal"], "CLOSED_INCOMPLETE")

    def test_current_phase_reading_agrees_between_status_and_phase_record(self) -> None:
        """Snapshot: re-pointed at the reconciled reading rather than the unopened tree.

        Still fails if `contracts/phases.json` and `STATUS.yaml` disagree about
        which phase, if any, is open.
        """
        data = phase_context.collect(ROOT)
        self.assertEqual(data["defects"], [])

    def test_prepared_profile_is_non_authoritative_and_recurrent(self) -> None:
        prd = (ROOT / "PRD.md").read_text(encoding="utf-8")
        spec = (ROOT / "SPEC.md").read_text(encoding="utf-8")
        self.assertIn("Prepared Phase 1.5 qualification profile", prd)
        self.assertIn("Phase 1.5 is open", prd)
        for criterion in ("P15-Q1", "P15-Q2", "P15-Q3", "P15-Q4"):
            self.assertIn(criterion, prd)
            self.assertIn(criterion, spec)
        self.assertIn("candidate next Definition", prd)
        self.assertIn("gains no standing or authority", spec)

    def test_all_p15_normative_predicates_have_discriminating_fixture_pairs(self) -> None:
        report = sov_opening_readiness.commissioning_instrument(ROOT)
        self.assertEqual(report["predicates_total"], 12)
        self.assertEqual(report["predicates_covered"], 12)
        self.assertEqual(report["open"], [])
        self.assertEqual(report["defects"], [])
        self.assertTrue(report["closed"])

    def test_opening_rehearsal_requires_the_p15_instrument(self) -> None:
        instrument = sov_opening_readiness.commissioning_instrument(ROOT)
        self.assertTrue(instrument["closed"])
        self.assertEqual(instrument["predicates_covered"], 12)


if __name__ == "__main__":
    unittest.main()
