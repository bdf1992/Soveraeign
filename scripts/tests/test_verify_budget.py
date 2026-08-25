"""Checks for the graded verification budget.

Grading a gate is the kind of change that quietly turns a rule into advice, so
the case that matters most here is the defeating one: past the slowest ceiling
no grade is earned, and the overrun still enters the failure list. If that ever
stops holding, the budget has become a suggestion and this file is how anyone
finds out.

The second structural case is drift. `BUDGET_SECONDS` is derived from the last
band rather than written twice, because two declarations of one number diverge
and the divergence is silent.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS))

import verify  # noqa: E402
from sovverify.checks import CHECKS  # noqa: E402


class Bands(unittest.TestCase):
    def test_the_ceiling_is_the_slowest_band_not_a_second_declaration(self):
        self.assertEqual(verify.BUDGET_SECONDS, verify.BUDGET_GRADES[-1][1])

    def test_bands_run_fastest_first(self):
        ceilings = [ceiling for _, ceiling in verify.BUDGET_GRADES]
        self.assertEqual(ceilings, sorted(ceilings))

    def test_each_ceiling_is_inclusive(self):
        for name, ceiling in verify.BUDGET_GRADES:
            with self.subTest(band=name):
                self.assertEqual(verify.grade(ceiling), name)

    def test_a_moment_past_a_ceiling_drops_one_band(self):
        self.assertEqual(verify.grade(3.0), "PLATINUM")
        self.assertEqual(verify.grade(3.001), "GOLD")
        self.assertEqual(verify.grade(6.001), "SILVER")

    def test_every_graded_run_is_a_passing_run(self):
        """Nothing may earn a grade and still exceed the budget."""
        for wall in (0.5, 3.0, 3.001, 6.0, 6.001, 15.0):
            with self.subTest(wall=wall):
                self.assertIsNotNone(verify.grade(wall))
                self.assertLessEqual(wall, verify.BUDGET_SECONDS)


class Reporting(unittest.TestCase):
    def test_a_graded_line_names_the_next_faster_band(self):
        line = verify.budget_line(4.011)
        self.assertIn("GOLD", line)
        self.assertIn("PLATINUM needs 3.000s or less", line)

    def test_the_fastest_band_names_no_faster_one(self):
        line = verify.budget_line(1.2)
        self.assertIn("PLATINUM", line)
        self.assertNotIn("needs", line)


class PastTheCeiling(unittest.TestCase):
    """The defeating case: grading must not turn the budget into advice."""

    def test_over_the_ceiling_earns_no_grade(self):
        self.assertIsNone(verify.grade(verify.BUDGET_SECONDS + 0.001))

    def test_over_the_ceiling_reports_an_overrun_not_a_grade(self):
        line = verify.budget_line(verify.BUDGET_SECONDS + 0.001)
        self.assertIn("verification budget", line)
        self.assertNotIn("GRADE", line)

    def test_the_overrun_line_is_what_main_appends_to_failures(self):
        """Pins the wording main() puts in the failure list, so a rename is caught."""
        self.assertEqual(verify.budget_line(20.0),
                         f"verification budget (20.000s > {verify.BUDGET_SECONDS:.3f}s)")


class Scheduling(unittest.TestCase):
    """Keep the verified repair for the tooling critical path in the root table."""

    def test_repository_tooling_uses_the_sharded_runner(self):
        tooling = [check for check in CHECKS if check.name == "repository tooling tests"]
        self.assertEqual(len(tooling), 1)
        self.assertEqual(tooling[0].command,
                         [sys.executable, "scripts/run_tooling_tests.py"])
        self.assertIn("scripts/run_tooling_tests.py", tooling[0].observes)


if __name__ == "__main__":
    unittest.main()
