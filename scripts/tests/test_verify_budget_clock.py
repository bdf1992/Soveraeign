"""The catastrophic read prefers a check's own CPU seconds over its wall seconds.

`scripts/verify.py` flipped between exit 0 and exit 1 on an unchanged tree five
times in one day (2026-09-02): the "repository tooling tests" check read wall
times from 27.6s to 39.7s while 846 of 846 tests passed every time, on a
machine running a dozen other sessions. A wall reading taken on a contended
host measures the host, not the check (the same failure mode
`contracts/verification-budget.json` already records from PR #151), and
`catastrophic_confirm_alone` does not fix it: the isolated re-read is itself
taken on the same contended host.

`scripts/sovverify/clocks.py` already measures both clocks per check, so
`budget.judge` reads the catastrophic ceiling against `Reading.cpu` whenever
`Reading.measured` is true, and falls back to the wall reading only when it is
not. Debt, the wall-clock grade, and every other purpose are unchanged: they
still grade on wall, exactly as `decisions/0081` settled.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovverify import budget  # noqa: E402

TABLE = budget.load()
CEILING = float(TABLE["catastrophic_check_seconds"])


class CpuDecidesTheCatastrophe(unittest.TestCase):
    """The three readings a contended host can produce for one check."""

    def test_wall_past_ceiling_with_cpu_measured_under_it_raises_no_catastrophe(self) -> None:
        """The exact shape of the flake: wall crossed 30s, the work did not."""
        debts, catastrophes = budget.judge(
            [("repository tooling tests", CEILING + 9.7, 5.2, True)], TABLE)
        self.assertEqual(catastrophes, [])
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])
        # Wall still owes its debt against the check's own ceiling; unchanged.
        self.assertEqual(debts, [budget.Debt("repository tooling tests", CEILING + 9.7, 3.0)])

    def test_wall_and_cpu_both_past_ceiling_refuses(self) -> None:
        """A genuine pathological regression: the work itself, not the host, is slow."""
        table = {**TABLE, "catastrophic_confirm_alone": False}
        _, catastrophes = budget.judge(
            [("repository tooling tests", CEILING + 6.667, CEILING + 2.0, True)], table)
        self.assertEqual(catastrophes,
                         [budget.Catastrophe("repository tooling tests", CEILING + 2.0, CEILING)])
        self.assertEqual(budget.refusing(catastrophes, table), catastrophes)

    def test_no_measured_cpu_still_refuses_on_wall_alone(self) -> None:
        """The degraded path (`Reading.measured` false) keeps the old behavior exactly."""
        table = {**TABLE, "catastrophic_confirm_alone": False}
        _, catastrophes = budget.judge(
            [("repository tooling tests", CEILING + 1.0, None, False)], table)
        self.assertEqual(catastrophes,
                         [budget.Catastrophe("repository tooling tests", CEILING + 1.0, CEILING)])
        self.assertEqual(budget.refusing(catastrophes, table), catastrophes)

    def test_a_bare_wall_reading_keeps_grading_on_wall_as_before(self) -> None:
        """The two-element legacy shape (`name`, `wall`) still works unchanged."""
        _, catastrophes = budget.judge([("repository tooling tests", CEILING + 1.0)], TABLE)
        self.assertEqual(catastrophes,
                         [budget.Catastrophe("repository tooling tests", CEILING + 1.0, CEILING)])


if __name__ == "__main__":
    unittest.main()
