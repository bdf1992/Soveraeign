"""Cases for the recorded-baseline comparison.

The participant is expected to fail every requirement today. These cases prove
the check refuses on divergence from the record rather than on failure itself,
so a declared work surface stays green and a silent change does not.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sov_baseline  # noqa: E402


BASELINE = """# Asset Service Conformance Baseline

## Result

`FAIL`

| Requirement | Verdict | Observed defects |
| --- | --- | --- |
| PROD-I-1 · Propose | FAIL | proposal lacks cost record |
| PROD-I-2 · Remember | PASS | none |

## Standing

Prose that is not a table row.
"""


class RecordParsing(unittest.TestCase):
    def test_verdicts_parse_from_the_result_table(self):
        self.assertEqual(sov_baseline.recorded(BASELINE),
                         {"PROD-I-1": "FAIL", "PROD-I-2": "PASS"})

    def test_prose_and_headers_are_not_read_as_verdicts(self):
        self.assertNotIn("Requirement", sov_baseline.recorded(BASELINE))

    def test_a_baseline_with_no_table_records_nothing(self):
        self.assertEqual(sov_baseline.recorded("# Baseline\n\nNo table.\n"), {})


class Divergence(unittest.TestCase):
    def test_matching_verdicts_are_not_a_divergence(self):
        record = {"PROD-I-1": "FAIL", "PROD-I-2": "FAIL"}
        self.assertEqual(sov_baseline.compare(record, dict(record)), [])

    def test_nine_recorded_failures_still_failing_is_green(self):
        """The declared work surface must not turn the gate red."""
        record = {f"PROD-I-{n}": "FAIL" for n in range(1, 10)}
        self.assertEqual(sov_baseline.compare(record, dict(record)), [])

    def test_a_recorded_pass_that_now_fails_is_a_regression(self):
        defects = sov_baseline.compare({"PROD-I-1": "PASS"}, {"PROD-I-1": "FAIL"})
        self.assertIn("regressed", " ".join(defects))

    def test_a_recorded_failure_that_now_passes_still_refuses(self):
        """Good news is still divergence: the record must move with reality."""
        defects = sov_baseline.compare({"PROD-I-1": "FAIL"}, {"PROD-I-1": "PASS"})
        self.assertIn("improved", " ".join(defects))
        self.assertIn("BASELINE.md", " ".join(defects))

    def test_a_requirement_graded_but_never_recorded_is_reported(self):
        defects = sov_baseline.compare({}, {"PROD-I-9": "FAIL"})
        self.assertIn("does not record it", " ".join(defects))

    def test_a_requirement_recorded_but_not_graded_is_reported(self):
        defects = sov_baseline.compare({"PROD-I-9": "FAIL"}, {})
        self.assertIn("did not grade it", " ".join(defects))


class AgainstTheRepository(unittest.TestCase):
    def test_the_checked_in_baseline_records_nine_requirements(self):
        record = sov_baseline.recorded(sov_baseline.BASELINE.read_bytes().decode("utf-8"))
        self.assertEqual(len(record), 9)

    # The live participant run is deliberately not repeated here. The
    # "participant against its baseline" check in scripts/verify.py performs it
    # once per verification run; duplicating it doubled the slowest cost in
    # scripts/tests for no additional coverage.


if __name__ == "__main__":
    unittest.main()
