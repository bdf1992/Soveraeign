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
import contextlib
import io
import json
import sys
import tempfile
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

    def test_every_confirmation_case_refuses_as_declared(self) -> None:
        """What actually blocks, which judge does not decide on its own."""
        for case in FIXTURES["confirmation_cases"]:
            with self.subTest(case=case["case_id"]):
                table = TABLE
                if "confirm_alone" in case:
                    table = {**TABLE,
                             "catastrophic": {**TABLE["catastrophic"],
                                              "confirm_alone": case["confirm_alone"]}}
                suspected = [budget.Catastrophe(*row) for row in case["catastrophes"]]
                refusing = budget.refusing(suspected, table)
                self.assertEqual([entry.check for entry in refusing],
                                 case["expect_refusing"])

    def test_the_confirmation_corpus_covers_both_verdicts(self) -> None:
        """A corpus where every suspicion confirmed would not test the step at all."""
        outcomes = {
            "refuses": any(c["expect_refusing"] for c in FIXTURES["confirmation_cases"]),
            "clears": any(not c["expect_refusing"] for c in FIXTURES["confirmation_cases"]),
        }
        self.assertEqual(outcomes, dict.fromkeys(outcomes, True))

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
        ceiling = budget.catastrophic_for("anything unbaselined", TABLE)
        _, catastrophes = budget.judge([("anything unbaselined", ceiling + 0.001)], TABLE)
        self.assertEqual(len(catastrophes), 1)

    def test_every_catastrophic_ceiling_is_far_above_the_check_s_own_ceiling(self) -> None:
        """It must be unreachable by host load, or it becomes the old gate again.

        The margin the old absolute held against the largest named ceiling was
        5x. Per check the weakest margin the current table holds is 3.33x, so 3x
        is asserted: enough to keep the property, and derived from the table
        rather than chosen to be passed.
        """
        for check, named in TABLE["check_ceilings"]["named"].items():
            with self.subTest(check=check):
                self.assertGreaterEqual(budget.catastrophic_for(check, TABLE),
                                        float(named) * 3)

    def test_a_derived_ceiling_is_a_multiple_of_what_the_check_costs(self) -> None:
        """The property an absolute number could not hold as the suite grew."""
        factor = float(TABLE["catastrophic"]["factor"])
        for check, baseline in TABLE["catastrophic"]["baselines"].items():
            with self.subTest(check=check):
                derived = budget.catastrophic_for(check, TABLE)
                self.assertGreaterEqual(derived, float(baseline) * factor - 1e-9)

    def test_the_floor_stops_a_small_baseline_collapsing_its_ceiling(self) -> None:
        """Three times a 0.17s check is 0.51s, which ordinary noise would trip."""
        floor = float(TABLE["catastrophic"]["floor_seconds"])
        for check in TABLE["catastrophic"]["baselines"]:
            with self.subTest(check=check):
                self.assertGreaterEqual(budget.catastrophic_for(check, TABLE), floor)

    def test_the_suite_at_its_recorded_baseline_does_not_refuse(self) -> None:
        """The reading that refused before this change, and must not now."""
        check = "repository tooling tests"
        baseline = budget.baseline_for(check, TABLE)
        _, catastrophes = budget.judge([(check, baseline)], TABLE)
        self.assertEqual(catastrophes, [])

    def test_every_baseline_belongs_to_a_check_that_exists(self) -> None:
        """A baseline for a renamed or deleted check derives a ceiling for nothing."""
        names = {check.name for check in CHECKS}
        self.assertEqual(sorted(set(TABLE["catastrophic"]["baselines"]) - names), [])

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

    def test_check_names_are_unique(self) -> None:
        """Two checks sharing a name would collapse in more than one place.

        `confirm_alone` looks a suspect up by name, and `demoted` compares
        catastrophes by value; duplicates would silently re-read the wrong check
        and mis-attribute the debt of the one that cleared.
        """
        names = [check.name for check in CHECKS]
        self.assertEqual(sorted(names), sorted(set(names)))


def _table(**catastrophic: object) -> dict:
    """The live table with its catastrophic block overridden."""
    return {**TABLE, "catastrophic": {**TABLE["catastrophic"], **catastrophic}}


class TheGateReachesTheExitCode(unittest.TestCase):
    """The wiring from a confirmed catastrophe to exit 1, run end to end.

    Every other case here grades a function. None of them grades the path from
    `budget.refusing` to the number `main` returns, and that path is the only
    blocking timing condition in the repository. Deleting one line of it left
    every test in the suite green, which is how a gate becomes decoration: the
    parts are all tested and nothing tests that they are still connected.

    `main` is driven in process against a substituted check list, so this costs
    a second or two rather than a verification run.
    """

    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.tally = Path(self._dir.name) / "runs.txt"
        self.slow = self._stand_in("a check that takes a moment", self.tally)
        self.other = self._stand_in("another check that takes a moment",
                                    Path(self._dir.name) / "other.txt")
        self._checks = verify.CHECKS
        self._budget = verify.BUDGET_TABLE
        verify.CHECKS = [self.slow]

    def tearDown(self) -> None:
        verify.CHECKS = self._checks
        verify.BUDGET_TABLE = self._budget
        self._dir.cleanup()

    @staticmethod
    def _crowded_stand_in(name: str, tally: Path) -> "verify.Check":
        """A stand-in slow on its first run and fast on every one after.

        It stands for the check this whole step exists for: over the ceiling in
        the pool, under it alone. Without one, every case here has its suspects
        agree, and a gate that refuses only when they all agree — or when a
        majority do — passes. That rule is the plausible bad edit, because it is
        the same sentence that motivates confirming at all, applied one level
        too high.
        """
        return verify.Check(
            name,
            [sys.executable, "-c",
             f"import pathlib, time; p = pathlib.Path(r'{tally}'); "
             f"first = not p.exists(); "
             f"p.open('a').write('ran\\n'); "
             f"time.sleep(0.25 if first else 0.0)"],
            ROOT, "slow once, then fast: over the ceiling pooled and under it alone", ())

    @staticmethod
    def _stand_in(name: str, tally: Path) -> "verify.Check":
        """A check with a known cost that records every time it is executed.

        The tally is what proves the isolated re-reading is a fresh run of this
        check's own command. Asserting on the report's wording cannot: the
        phrase 're-run alone' is printed from the `alone` field, so it appears
        whether or not anything was re-run.
        """
        return verify.Check(
            name,
            [sys.executable, "-c",
             f"import time, pathlib; time.sleep(0.4); "
             f"pathlib.Path(r'{tally}').open('a').write('ran\\n')"],
            ROOT, "a stand-in with a known cost, so the ceiling decides and not the check",
            ())

    def _ran(self, tally: Path | None = None) -> int:
        tally = tally or self.tally
        return len(tally.read_text(encoding="utf-8").splitlines()) if tally.exists() else 0

    def _run(self, table: dict) -> tuple[int, str]:
        verify.BUDGET_TABLE = table
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = verify.main([])
        return code, buffer.getvalue()

    def test_a_confirmed_catastrophe_makes_the_run_exit_one(self) -> None:
        code, output = self._run(_table(floor_seconds=0.2, unbaselined_seconds=0.2,
                                        confirm_alone=True, blocks=True))
        self.assertEqual(code, 1)
        self.assertIn("catastrophic ceiling", output)
        self.assertIn("re-run alone", output)

    def test_the_isolated_reading_is_a_fresh_run_of_the_check_s_own_command(self) -> None:
        """Twice: once in the pool, once alone. The claim the whole step rests on."""
        self._run(_table(floor_seconds=0.2, unbaselined_seconds=0.2,
                         confirm_alone=True, blocks=True))
        self.assertEqual(self._ran(), 2)

    def test_a_check_inside_its_ceiling_is_never_re_read(self) -> None:
        """The other half: a passing run must cost nothing extra."""
        self._run(_table(floor_seconds=60.0, unbaselined_seconds=60.0,
                         confirm_alone=True, blocks=True))
        self.assertEqual(self._ran(), 1)

    def test_a_suspect_the_isolated_reading_clears_does_not_refuse(self) -> None:
        """The isolated reading must be used, not merely taken.

        The execution tally proves the re-run happens. It cannot prove the
        result is what decides: keeping the pooled reading after re-running
        passes every case that has its suspects confirm.
        """
        tally = Path(self._dir.name) / "crowded.txt"
        verify.CHECKS = [self._crowded_stand_in("a check that was merely crowded", tally)]
        code, output = self._run(_table(floor_seconds=0.2, unbaselined_seconds=0.2,
                                        confirm_alone=True, blocks=True))
        self.assertEqual(code, 0)
        self.assertIn("CROWDED:", output)
        self.assertIn("crowded, not changed", output)

    def test_one_confirmed_suspect_refuses_even_beside_a_cleared_one(self) -> None:
        """A real regression must not be excused by an unrelated check being crowded.

        'Several checks were over at once, so the host was busy' is exactly the
        reasoning behind confirming alone, and it is wrong applied to the set:
        each suspect answers for itself.
        """
        tally = Path(self._dir.name) / "crowded.txt"
        crowded = self._crowded_stand_in("a check that was merely crowded", tally)
        verify.CHECKS = [crowded, self.slow]
        code, output = self._run(_table(floor_seconds=0.2, unbaselined_seconds=0.2,
                                        confirm_alone=True, blocks=True))
        self.assertEqual(code, 1)
        failure = output.split("FAIL: ")[-1]
        self.assertIn(self.slow.name, failure)
        self.assertNotIn(crowded.name, failure)
        self.assertIn("CROWDED:", output)

    def test_two_suspects_both_reach_the_failure(self) -> None:
        """One-at-a-time cases cannot see a gate that refuses only the first.

        `failed.extend(... refusing[:1])`, or a rule that gives up when several
        checks are over at once, would pass every other case here and let two
        simultaneous regressions through while blocking one.
        """
        verify.CHECKS = [self.slow, self.other]
        code, output = self._run(_table(floor_seconds=0.2, unbaselined_seconds=0.2,
                                        confirm_alone=True, blocks=True))
        self.assertEqual(code, 1)
        self.assertIn(self.slow.name, output)
        self.assertIn(self.other.name, output)
        failure = output.split("FAIL: ")[-1]
        self.assertIn(self.slow.name, failure)
        self.assertIn(self.other.name, failure)

    def test_a_check_inside_its_ceiling_makes_the_run_exit_zero(self) -> None:
        """Without this, the case above would pass on a run that always failed."""
        code, output = self._run(_table(floor_seconds=60.0, unbaselined_seconds=60.0,
                                        confirm_alone=True, blocks=True))
        self.assertEqual(code, 0)
        self.assertNotIn("catastrophic ceiling", output)

    def test_no_suspect_leaves_confirmation_without_a_reading(self) -> None:
        """The postcondition that makes any future skipped re-read fail closed.

        Cases here bound how many suspects a run has, so a rule that skips
        re-reads above some number is invisible to every case below it and adding
        one more only moves the boundary. This asserts the property instead: with
        confirmation on, nothing returns from `confirm_alone` still carrying no
        isolated reading, whatever reason it might have been skipped for.
        """
        suspects = [budget.Catastrophe(f"suspect {index}", 99.0, 10.0) for index in range(5)]
        confirmed = verify.confirm_alone(suspects, [])
        self.assertTrue(all(entry.alone is not None for entry in confirmed))
        self.assertEqual(len(budget.refusing(confirmed, TABLE)), 5)

    def test_a_suspect_naming_no_known_check_still_refuses(self) -> None:
        """The branch no run reaches, pinned in the safe direction.

        `confirm_alone` builds its lookup from the same results the suspects came
        from, so a suspect with no matching check cannot occur today. If it ever
        can, `refusing` discards any entry carrying no isolated reading - so the
        careless branch is the one where a check nobody could re-read quietly
        stops refusing. It stands on the reading there is instead.
        """
        orphan = budget.Catastrophe("a check that is not in the results", 99.0, 10.0)
        confirmed = verify.confirm_alone([orphan], [])
        self.assertEqual(confirmed[0].alone, 99.0)
        self.assertEqual([entry.check for entry in budget.refusing(confirmed, TABLE)],
                         ["a check that is not in the results"])

    def test_the_declared_switch_turns_the_gate_off(self) -> None:
        """`blocks` is read rather than described; a switch that switches nothing lies."""
        code, _ = self._run(_table(floor_seconds=0.2, unbaselined_seconds=0.2,
                                   confirm_alone=True, blocks=False))
        self.assertEqual(code, 0)


class ClearedSuspectsKeepTheirDebt(unittest.TestCase):
    """A catastrophe that clears refuses nothing, so it owes what it always owed."""

    def test_a_cleared_suspect_is_returned_to_the_debt_list(self) -> None:
        suspect = budget.Catastrophe("Asset Service reference tests", 60.0, 49.98, 5.0)
        refused = budget.refusing([suspect], TABLE)
        self.assertEqual(refused, [])
        debts = budget.demoted([suspect], refused, TABLE)
        self.assertEqual([list(entry) for entry in debts],
                         [["Asset Service reference tests", 60.0, 4.0]])

    def test_a_confirmed_suspect_is_not_also_debt(self) -> None:
        """The rule judge already held: one regression is reported once."""
        suspect = budget.Catastrophe("Asset Service reference tests", 60.0, 49.98, 59.0)
        refused = budget.refusing([suspect], TABLE)
        self.assertEqual([entry.check for entry in refused],
                         ["Asset Service reference tests"])
        self.assertEqual(budget.demoted([suspect], refused, TABLE), [])


class BaselineDrift(unittest.TestCase):
    """A baseline set too high raises a ceiling, and nothing else notices."""

    def test_a_check_measuring_far_under_its_baseline_is_named(self) -> None:
        lines = budget.baseline_drift([("repository tooling tests", 1.0)], TABLE)
        self.assertEqual(len(lines), 1)
        self.assertIn("repository tooling tests", lines[0])
        self.assertIn("32.130s baseline", lines[0])

    def test_a_check_measuring_near_its_baseline_is_not(self) -> None:
        baseline = budget.baseline_for("repository tooling tests", TABLE)
        self.assertEqual(budget.baseline_drift(
            [("repository tooling tests", baseline)], TABLE), [])

    def test_an_unbaselined_check_cannot_drift(self) -> None:
        self.assertEqual(budget.baseline_drift([("nobody named this", 0.001)], TABLE), [])

    def test_a_check_measuring_far_over_its_baseline_is_named(self) -> None:
        """The other direction, and the one the cliff cannot catch cleanly.

        A doubling is debt and not a refusal at factor 3.0, so this line is the
        only place a run says a check costs materially more than it did.
        """
        lines = budget.baseline_drift([("Asset Service reference tests", 45.0)], TABLE)
        self.assertEqual(len(lines), 1)
        self.assertIn("costs materially more", lines[0])
        self.assertIn("2.70x", lines[0])

    def test_a_small_baseline_is_not_compared_at_all(self) -> None:
        """Scheduling noise on a fifth of a second is not drift.

        Measured: baselines of 0.21s and 0.22s produced false 2.28x and 2.44x
        readings on one loaded run of unchanged bytes.
        """
        small = min(TABLE["catastrophic"]["baselines"].items(), key=lambda kv: kv[1])
        self.assertLess(small[1], float(TABLE["catastrophic"]["baseline_drift"]
                                        ["floor_seconds"]))
        self.assertEqual(budget.baseline_drift([(small[0], small[1] * 10)], TABLE), [])


class DriftReachesTheReport(unittest.TestCase):
    """The drift lines reach the run's output, not just the function's return."""

    def setUp(self) -> None:
        self._checks = verify.CHECKS
        self._budget = verify.BUDGET_TABLE

    def tearDown(self) -> None:
        verify.CHECKS = self._checks
        verify.BUDGET_TABLE = self._budget

    def test_a_drifting_check_is_named_in_the_report(self) -> None:
        name = "repository hygiene"
        verify.CHECKS = [verify.Check(
            name, [sys.executable, "-c", "pass"], ROOT,
            "a stand-in borrowing a baselined name, so drift has something to compare", ())]
        verify.BUDGET_TABLE = {**TABLE, "catastrophic": {
            **TABLE["catastrophic"], "floor_seconds": 60.0, "unbaselined_seconds": 60.0,
            "baseline_drift": {**TABLE["catastrophic"]["baseline_drift"],
                               "floor_seconds": 0.5}}}
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = verify.main([])
        output = buffer.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("BASELINE:", output)
        self.assertIn(name, output)


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
