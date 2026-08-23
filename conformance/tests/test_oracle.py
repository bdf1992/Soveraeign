from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import importlib.util
import io
import json
import sys
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

SMUGGLED = {
    "participant_verdict": "PASS",
    "verdict": "PASS",
    "expected_oracle": "PASS",
    "suite": "PASS",
    "defects": [],
    "passed": True,
}


class SmuggledVerdictFieldsChangeNothing(unittest.TestCase):
    """A submitter may attach richer telemetry; none of it may reach the verdict."""

    def setUp(self):
        self.cases = json.loads((ROOT / "oracle-controls.json").read_text(encoding="utf-8"))

    def test_no_check_reads_a_submitted_verdict(self):
        for case in self.cases:
            check = runner.CHECKS[case["requirement"]]
            honest = check(case["observed"])
            smuggled = check({**case["observed"], **SMUGGLED})
            self.assertEqual(smuggled, honest, case["id"])

    def test_every_defeating_control_still_fails_when_it_claims_to_pass(self):
        defeating = [case for case in self.cases if case["polarity"] == "defeating"]
        self.assertEqual({case["requirement"] for case in defeating}, runner.REQUIREMENTS)
        for case in defeating:
            check = runner.CHECKS[case["requirement"]]
            self.assertTrue(check({**case["observed"], **SMUGGLED}), case["id"])


def participant_case_id(control):
    """Derive a stable participant case id. Keyed on the control id, not the requirement:
    PROD-I-5 carries two control pairs, so a requirement-keyed id collides."""
    return f"RUN-{control['id']}"


def participant_report(controls, polarity):
    """One observation per control of the given polarity, addressed as a participant would."""
    return [
        {"case_id": participant_case_id(case), "observed": case["observed"]}
        for case in controls
        if case["polarity"] == polarity
    ]


def participant_cases(controls, expected_oracle=None):
    """A narrative file shaped like scenarios.json, one entry per positive control."""
    cases = []
    for case in controls:
        if case["polarity"] != "positive":
            continue
        entry = {"id": participant_case_id(case), "requirement": case["requirement"],
                 "polarity": "participant"}
        if expected_oracle is not None:
            entry["expected_oracle"] = expected_oracle
        cases.append(entry)
    return cases


class ObservationReportReading(unittest.TestCase):
    """The loader refuses what it cannot read as submitted; it never resolves ambiguity."""

    def setUp(self):
        self.controls = json.loads((ROOT / "oracle-controls.json").read_text(encoding="utf-8"))
        self.honest = participant_report(self.controls, "positive")

    def load(self, payload):
        with TemporaryDirectory() as raw:
            path = Path(raw) / "observations.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return runner.observations_by_id(path, [])

    def test_honest_report_loads(self):
        loaded = self.load(self.honest)
        self.assertEqual(len(loaded), len(self.honest))
        self.assertTrue(all(isinstance(observed, dict) for observed in loaded.values()))

    def test_repeated_case_id_is_refused_not_resolved(self):
        smuggle = [{"case_id": self.honest[0]["case_id"], "observed": {}}] + self.honest
        with self.assertRaises(runner.ObservationError) as caught:
            self.load(smuggle)
        self.assertIn("repeats an observation", str(caught.exception))

    def test_report_must_be_an_array(self):
        with self.assertRaises(runner.ObservationError):
            self.load({"suite": "PASS", "results": self.honest})

    def test_entry_without_observed_is_refused(self):
        with self.assertRaises(runner.ObservationError):
            self.load([{"case_id": "RUN-PROD-I-1"}])

    def test_observed_must_be_an_object(self):
        with self.assertRaises(runner.ObservationError):
            self.load([{"case_id": "RUN-PROD-I-1", "observed": "PASS"}])

    def test_entry_without_case_id_is_refused(self):
        with self.assertRaises(runner.ObservationError):
            self.load([{"observed": {}}])

    def test_case_file_is_held_to_the_same_reading(self):
        duplicated = [{"id": "CONF-X", "observed": {}}, {"id": "CONF-X", "observed": {}}]
        with self.assertRaises(runner.ObservationError) as caught:
            runner.observations_by_id(None, duplicated)
        self.assertIn("case file", str(caught.exception))


class ParticipantRunVerdicts(unittest.TestCase):
    """End to end: the submitter supplies observations, never the verdict."""

    def setUp(self):
        self.controls = json.loads((ROOT / "oracle-controls.json").read_text(encoding="utf-8"))

    def run_oracle(self, cases, observations):
        with TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "cases.json").write_text(json.dumps(cases), encoding="utf-8")
            (root / "obs.json").write_text(json.dumps(observations), encoding="utf-8")
            argv = ["run.py", "--cases", str(root / "cases.json"),
                    "--observations", str(root / "obs.json")]
            buffer = io.StringIO()
            with patch.object(sys, "argv", argv), redirect_stdout(buffer):
                code = runner.main()
            return code, buffer.getvalue()

    def test_honest_positive_run_passes(self):
        cases = participant_cases(self.controls)
        code, report = self.run_oracle(cases, participant_report(self.controls, "positive"))
        self.assertEqual(code, 0)
        self.assertIn(f"SUITE   PASS cases={len(cases)} coverage_gaps=0", report)

    def test_duplicated_observation_invalidates_the_whole_run(self):
        observations = participant_report(self.controls, "positive")
        smuggle = [{"case_id": observations[0]["case_id"], "observed": {}}] + observations
        code, report = self.run_oracle(participant_cases(self.controls), smuggle)
        self.assertEqual(code, 1)
        self.assertIn("SUITE   INVALID", report)
        self.assertNotIn("SUITE   PASS", report)

    def test_expected_oracle_in_the_case_file_cannot_pass_a_defeating_run(self):
        cases = participant_cases(self.controls, expected_oracle="PASS")
        for case, control in zip(cases, [c for c in self.controls if c["polarity"] == "positive"]):
            defeat = next(c for c in self.controls
                          if c["polarity"] == "defeating" and c["requirement"] == control["requirement"])
            case["id"] = participant_case_id(defeat)
        code, report = self.run_oracle(cases, participant_report(self.controls, "defeating"))
        self.assertEqual(code, 1)
        self.assertIn("SUITE   FAIL", report)


if __name__ == "__main__":
    unittest.main()
