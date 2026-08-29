"""Checks for the verification budget after decisions/0081 and #148/C0027.

Wall-clock readings never refuse because they describe a host at an instant, and
ordinary per-check overruns remain attributed debt. Catastrophic pressure still
exists, but a pooled per-check wall time is now only a suspicion: when the table
requires confirmation, the check must cross the catastrophic ceiling again when
re-read alone before verification may refuse the run.

Cases are driven from conformance/fixtures/verification-budget/cases.json, which
holds the declared positive and defeating corpus; this file adds structural
wiring cases a fixture cannot state by itself.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
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

    def test_confirmation_cases_declare_what_actually_refuses(self) -> None:
        for case in FIXTURES["confirmation_cases"]:
            with self.subTest(case=case["case_id"]):
                catastrophes = [budget.Catastrophe(*row) for row in case["catastrophes"]]
                refusing = budget.refusing(catastrophes, TABLE)
                demoted = budget.demoted(catastrophes, refusing, TABLE)
                self.assertEqual([list(entry) for entry in refusing],
                                 [list(row) for row in case["expect_refusing"]])
                self.assertEqual([list(entry) for entry in demoted],
                                 [list(row) for row in case["expect_demoted_debts"]])

    def test_the_corpus_carries_a_case_for_each_outcome(self) -> None:
        """A corpus that never produced a catastrophe would prove nothing blocks."""
        outcomes = {
            "graded": any(c["expect_grade"] for c in FIXTURES["cases"]),
            "ungraded": any(c["expect_grade"] is None for c in FIXTURES["cases"]),
            "debt": any(c["expect_debts"] for c in FIXTURES["cases"]),
            "catastrophe": any(c["expect_catastrophes"] for c in FIXTURES["cases"]),
            "confirmed_refusal": any(c["expect_refusing"] for c in FIXTURES["confirmation_cases"]),
            "cleared_suspicion": any(not c["expect_refusing"]
                                     for c in FIXTURES["confirmation_cases"]),
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
    """Catastrophic pressure survives without mistaking pooled contention for proof."""

    def test_past_the_catastrophic_ceiling_creates_a_suspicion(self) -> None:
        ceiling = float(TABLE["catastrophic_check_seconds"])
        _, catastrophes = budget.judge([("anything", ceiling + 0.001)], TABLE)
        self.assertEqual(len(catastrophes), 1)
        self.assertIsNone(catastrophes[0].alone)

    def test_confirmation_is_declared(self) -> None:
        self.assertTrue(TABLE["catastrophic_confirm_alone"])
        self.assertTrue(budget.confirms_alone(TABLE))

    def test_unconfirmed_pooled_overrun_does_not_refuse(self) -> None:
        ceiling = float(TABLE["catastrophic_check_seconds"])
        _, catastrophes = budget.judge([("anything", ceiling + 5.0)], TABLE)
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])

    def test_confirmed_isolated_overrun_still_refuses(self) -> None:
        ceiling = float(TABLE["catastrophic_check_seconds"])
        catastrophe = budget.Catastrophe("anything", ceiling + 5.0, ceiling,
                                        ceiling + 1.0)
        self.assertEqual(budget.refusing([catastrophe], TABLE), [catastrophe])

    def test_cleared_catastrophe_returns_as_attributed_debt(self) -> None:
        catastrophe = budget.Catastrophe("Asset Service reference tests", 36.667, 30.0, 12.0)
        refused = budget.refusing([catastrophe], TABLE)
        self.assertEqual(refused, [])
        self.assertEqual(budget.demoted([catastrophe], refused, TABLE),
                         [budget.Debt("Asset Service reference tests", 36.667, 4.0)])

    def test_the_catastrophic_ceiling_is_far_above_any_named_ceiling(self) -> None:
        """Confirmation fixes contention; the catastrophic threshold still stays exceptional."""
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


class ConfirmationWiring(unittest.TestCase):
    """The root verifier really performs the isolation the budget contract requires."""

    class Reading:
        wall = 12.0
        output = "isolated output\n"

        @staticmethod
        def report() -> str:
            return "12.000s wall"

    def test_confirm_alone_reruns_each_suspect_after_the_pool(self) -> None:
        check = next(check for check in CHECKS if check.name == "Asset Service reference tests")
        suspect = budget.Catastrophe(check.name, 36.667, 30.0)
        pooled = [(check, self.Reading())]
        with patch.object(verify, "run_check", return_value=(check, self.Reading())) as rerun:
            confirmed = verify.confirm_alone([suspect], pooled)
        rerun.assert_called_once_with(check)
        self.assertEqual(confirmed, [suspect._replace(alone=12.0)])
        self.assertFalse(confirmed[0].confirmed())

    def test_missing_check_fails_closed_instead_of_clearing_the_suspicion(self) -> None:
        suspect = budget.Catastrophe("no longer registered", 31.0, 30.0)
        confirmed = verify.confirm_alone([suspect], [])
        self.assertEqual(confirmed[0].alone, 31.0)
        self.assertTrue(confirmed[0].confirmed())


class NoDrift(unittest.TestCase):
    """The table is the single declaration; verify.py restates none of its thresholds."""

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
