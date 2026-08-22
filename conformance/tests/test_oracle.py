from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("conformance_runner", ROOT / "run.py")
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class OracleTests(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads((ROOT / "oracle-controls.json").read_text(encoding="utf-8"))

    def test_every_requirement_has_positive_and_defeating_case(self):
        coverage = {requirement: set() for requirement in runner.REQUIREMENTS}
        for case in self.cases:
            coverage[case["requirement"]].add(case["polarity"])
        self.assertTrue(all(value == {"positive", "defeating"} for value in coverage.values()))

    def test_embedded_controls_match_expected_oracle(self):
        for case in self.cases:
            defects = runner.CHECKS[case["requirement"]](case["observed"])
            verdict = "FAIL" if defects else "PASS"
            self.assertEqual(verdict, case["expected_oracle"], case["id"])

    def test_oracle_does_not_accept_participant_verdict_field(self):
        case = next(item for item in self.cases if item["id"] == "CONF-I5-DEF")
        observed = dict(case["observed"])
        observed["participant_verdict"] = "PASS"
        self.assertTrue(runner.check_i5(observed))

    def test_authority_case_requires_both_claim_types(self):
        observed = {"attempts": [{
            "actor_kind": "MODEL", "authority_type": "VERIFICATION",
            "claim_type": "JUDGEMENT", "grant_live": True,
            "scope_matches": True, "budget_available": True,
            "outcome": "REFUSED", "receipt_id": "r1",
        }]}
        defects = runner.check_i5(observed)
        self.assertIn("authority scenario did not exercise both claim types", defects)
        self.assertIn("delegated verification claim did not commit", defects)

    def test_byom_requires_distinct_models_and_visible_provider_loss(self):
        observed = {
            "bindings": [],
            "unavailable_model": {"outcome": "COMMITTED", "silent_fallback": True},
            "local_record_operable": False,
        }
        defects = runner.check_i9(observed)
        self.assertIn("fewer than two model bindings were exercised", defects)
        self.assertIn("unavailable model triggered silent fallback", defects)
        self.assertIn("provider loss removed local record operation", defects)


if __name__ == "__main__":
    unittest.main()
