"""Wall accuses the catastrophic ceiling; a measured CPU reading only acquits it.

`scripts/verify.py` flipped between exit 0 and exit 1 on an unchanged tree five
times in one day (2026-09-02): the "repository tooling tests" check read wall
times from 27.6s to 39.7s while 846 of 846 tests passed every time, on a
machine running a dozen other sessions. A wall reading taken on a contended
host measures the host, not the check (the same failure mode
`contracts/verification-budget.json` already records from PR #151), and
`catastrophic_confirm_alone` does not fix it: the isolated re-read is itself
taken on the same contended host.

Preferring CPU over wall outright does not work either: that same check shards
across processes, and a later uncontended run measured 60.609s of CPU against
26.194s wall. Grading the accusation on CPU would make the ceiling stricter
for every check that shards, and would raise a suspicion wall never raised.
So the shape is narrower: wall accuses exactly as it does today, and a
measured CPU reading (`scripts/sovverify/clocks.py`) at or under the ceiling
acquits that accusation. CPU never raises a suspicion wall did not already
raise. Debt, the wall-clock grade, and every other purpose are unchanged: they
still grade on wall, exactly as `decisions/0081` settled.

That reading is correct for what it describes, but it cannot reach this case:
a check that shards across four processes always spends more CPU than wall, so
its CPU reading can never come in under a ceiling its wall already exceeded.
"repository tooling tests" also owns a named ceiling (3.0s) that already
carries this cost as attributed debt, so it now owns its own catastrophic
ceiling too (`check_ceilings.owns_its_catastrophe`,
`catastrophic_ceiling_for`) rather than sharing the flat backstop sized for a
check with no ceiling of its own. These cases now exercise wall-accuses,
cpu-acquits against that check's own derived ceiling, not the shared one.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovverify import budget  # noqa: E402

TABLE = budget.load()
CEILING = budget.catastrophic_ceiling_for("repository tooling tests", TABLE)


class WallAccusesCpuAcquits(unittest.TestCase):
    """The four readings a contended, sharding host can produce for one check."""

    def test_wall_over_and_cpu_under_acquits(self) -> None:
        """The exact shape of the flake: wall crossed the ceiling, the work did not."""
        debts, catastrophes = budget.judge(
            [("repository tooling tests", CEILING + 9.7, 5.2, True)], TABLE)
        self.assertEqual(catastrophes, [])
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])
        # Wall still owes its debt against the check's own ceiling; unchanged.
        self.assertEqual(debts, [budget.Debt("repository tooling tests", CEILING + 9.7, 3.0)])

    def test_wall_over_and_cpu_over_refuses(self) -> None:
        """A genuine pathological regression: the work itself, not the host, is slow."""
        table = {**TABLE, "catastrophic_confirm_alone": False}
        _, catastrophes = budget.judge(
            [("repository tooling tests", CEILING + 6.667, CEILING + 2.0, True)], table)
        self.assertEqual(catastrophes,
                         [budget.Catastrophe("repository tooling tests", CEILING + 2.0, CEILING)])
        self.assertEqual(budget.refusing(catastrophes, table), catastrophes)

    def test_wall_over_and_cpu_unmeasured_refuses_on_wall_alone(self) -> None:
        """The degraded path (`Reading.measured` false) keeps the old behavior exactly."""
        table = {**TABLE, "catastrophic_confirm_alone": False}
        _, catastrophes = budget.judge(
            [("repository tooling tests", CEILING + 1.0, None, False)], table)
        self.assertEqual(catastrophes,
                         [budget.Catastrophe("repository tooling tests", CEILING + 1.0, CEILING)])
        self.assertEqual(budget.refusing(catastrophes, table), catastrophes)

    def test_wall_under_raises_nothing_whatever_cpu_reads(self) -> None:
        """A check that shards across processes: CPU alone never gets to accuse."""
        debts, catastrophes = budget.judge(
            [("repository tooling tests", CEILING - 3.806, CEILING + 30.609, True)], TABLE)
        self.assertEqual(catastrophes, [])
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])
        # Wall still owes its own debt against the check's own ceiling, unrelated
        # to the catastrophic read this test exercises.
        self.assertEqual(debts,
                         [budget.Debt("repository tooling tests", CEILING - 3.806, 3.0)])

    def test_a_bare_wall_reading_keeps_grading_on_wall_as_before(self) -> None:
        """The two-element legacy shape (`name`, `wall`) still works unchanged."""
        _, catastrophes = budget.judge([("repository tooling tests", CEILING + 1.0)], TABLE)
        self.assertEqual(catastrophes,
                         [budget.Catastrophe("repository tooling tests", CEILING + 1.0, CEILING)])


if __name__ == "__main__":
    unittest.main()
