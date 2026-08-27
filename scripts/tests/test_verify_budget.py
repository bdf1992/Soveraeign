"""Checks for the verification budget after decisions/0081.

The rule under test inverted. Before, the structural case was that an overrun
entered the failure list, and this file existed so anyone could see if the budget
had become a suggestion. Now the case is the opposite: a wall-clock reading must
NOT refuse, because it measures the host at that instant and not the repository,
and an overrun on one check must be attributed to that check rather than to
whoever touched the repository next.

That leaves a real hazard, which `Pressure` covers: a budget that blocks nothing
applies no pressure and a suite grows without limit. Two things answer it - the
catastrophic per-check ceiling, which does refuse, and the requirement that debt
is computed, counted and named rather than passed over in silence.

Cases are driven from conformance/fixtures/verification-budget/cases.json, which
holds the declared positive and defeating corpus; this file adds only the
structural cases a fixture cannot state.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402
from sovverify import budget  # noqa: E402
from sovverify.checks import CHECKS  # noqa: E402

FIXTURES = json.loads(
    (ROOT / "conformance" / "fixtures" / "verification-budget" / "cases.json")
    .read_bytes().decode("utf-8"))
TABLE = budget.load()


class DeclaredCorpus(unittest.TestCase):
    """Every case in the fixture file, judged against the live table."""

    def test_every_case_grades_debts_and_catastrophes_as_declared(self) -> None:
        for case in FIXTURES["cases"]:
            with self.subTest(case=case["case_id"]):
                timings = [(name, seconds) for name, seconds in case["timings"]]
                debts, catastrophes = budget.judge(timings, TABLE)
                self.assertEqual(budget.grade(case["wall"], TABLE), case["expect_grade"])
                self.assertEqual([list(entry) for entry in debts],
                                 [list(row) for row in case["expect_debts"]])
                self.assertEqual([list(entry) for entry in catastrophes],
                                 [list(row) for row in case["expect_catastrophes"]])

    def test_the_corpus_carries_a_case_for_each_outcome(self) -> None:
        """A corpus that never produced a catastrophe would prove nothing blocks."""
        outcomes = {
            "graded": any(c["expect_grade"] for c in FIXTURES["cases"]),
            "ungraded": any(c["expect_grade"] is None for c in FIXTURES["cases"]),
            "debt": any(c["expect_debts"] for c in FIXTURES["cases"]),
            "catastrophe": any(c["expect_catastrophes"] for c in FIXTURES["cases"]),
        }
        self.assertEqual(outcomes, dict.fromkeys(outcomes, True))


class WallClockNeverRefuses(unittest.TestCase):
    """The change decisions/0081 makes, stated as its own cases."""

    def test_past_every_band_earns_no_grade(self) -> None:
        self.assertIsNone(verify.grade(verify.BUDGET_SECONDS + 0.001))

    def test_past_every_band_reports_debt_and_not_a_failure(self) -> None:
        line = verify.budget_line(verify.BUDGET_SECONDS + 0.001)
        self.assertIn("DEBT", line)
        self.assertNotIn("GRADE", line)

    def test_a_wall_time_produces_no_catastrophe_however_large(self) -> None:
        """Wall time is the sum of concurrent work; only a single check can block."""
        _, catastrophes = budget.judge([("repository hygiene", 1.0)], TABLE)
        self.assertEqual(catastrophes, [])

    def test_the_declared_table_says_the_wall_clock_does_not_block(self) -> None:
        self.assertFalse(TABLE["wall_clock"]["blocks"])
        self.assertFalse(TABLE["check_ceilings"]["blocks"])


class Pressure(unittest.TestCase):
    """The hazard the change creates: a budget that blocks nothing applies nothing."""

    def test_one_catastrophic_check_still_refuses(self) -> None:
        ceiling = float(TABLE["catastrophic_check_seconds"])
        _, catastrophes = budget.judge([("anything", ceiling + 0.001)], TABLE)
        self.assertEqual(len(catastrophes), 1)

    def test_the_catastrophic_ceiling_is_far_above_any_named_ceiling(self) -> None:
        """It must be unreachable by host load, or it becomes the old gate again."""
        named = list(TABLE["check_ceilings"]["named"].values())
        self.assertGreater(float(TABLE["catastrophic_check_seconds"]), max(named) * 5)

    def test_debt_is_counted_and_named_rather_than_passed_over(self) -> None:
        debts, _ = budget.judge([("Asset Service reference tests", 11.7)], TABLE)
        lines = budget.report(debts, "GRADE: SILVER at 11.749s", TABLE)
        body = "\n".join(lines)
        self.assertIn("BUDGET DEBT: 1 check(s)", body)
        self.assertIn("Asset Service reference tests", body)
        self.assertIn("11.700s", body)

    def test_a_clean_run_says_so_rather_than_staying_silent(self) -> None:
        """Silence would read the same as a run whose debt nobody computed."""
        lines = budget.report([], "GRADE: PLATINUM at 2.400s, the fastest band", TABLE)
        self.assertIn("BUDGET: every check inside its ceiling", "\n".join(lines))

    def test_every_named_ceiling_belongs_to_a_check_that_exists(self) -> None:
        """A ceiling on a renamed or deleted check is pressure on nothing."""
        names = {check.name for check in CHECKS}
        self.assertEqual(sorted(set(TABLE["check_ceilings"]["named"]) - names), [])


class NoDrift(unittest.TestCase):
    """The table is the single declaration; verify.py restates none of it."""

    def test_verify_derives_its_bands_from_the_table(self) -> None:
        self.assertEqual(list(verify.BUDGET_GRADES), budget.grades(TABLE))

    def test_the_slowest_band_is_the_derived_ceiling(self) -> None:
        self.assertEqual(verify.BUDGET_SECONDS, verify.BUDGET_GRADES[-1][1])

    def test_bands_run_fastest_first(self) -> None:
        ceilings = [ceiling for _, ceiling in verify.BUDGET_GRADES]
        self.assertEqual(ceilings, sorted(ceilings))

    def test_each_band_ceiling_is_inclusive(self) -> None:
        for name, ceiling in verify.BUDGET_GRADES:
            with self.subTest(band=name):
                self.assertEqual(verify.grade(ceiling), name)

    def test_a_graded_line_names_the_next_faster_band(self) -> None:
        line = verify.budget_line(4.011)
        self.assertIn("GOLD", line)
        self.assertIn("PLATINUM needs 3.000s", line)

    def test_the_fastest_band_names_no_faster_one(self) -> None:
        line = verify.budget_line(1.2)
        self.assertIn("PLATINUM", line)
        self.assertNotIn("needs", line)


class Scheduling(unittest.TestCase):
    """Keep the verified repair for the tooling critical path in the root table."""

    def test_repository_tooling_uses_the_sharded_runner(self) -> None:
        tooling = [check for check in CHECKS if check.name == "repository tooling tests"]
        self.assertEqual(len(tooling), 1)
        self.assertEqual(tooling[0].command,
                         [sys.executable, "scripts/run_tooling_tests.py"])
        self.assertIn("scripts/run_tooling_tests.py", tooling[0].observes)


if __name__ == "__main__":
    unittest.main()
