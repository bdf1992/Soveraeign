"""A check that carries a named ceiling owns its own catastrophic ceiling.

`contracts/verification-budget.json` applied one flat `catastrophic_check_seconds`
(30.0s) to every check, sized for a check with no ceiling of its own. That
refused "repository tooling tests" twice over: it already carries a named
ceiling (3.0s) that Bdo accepted as debt on 2026-08-27 knowing it was
exceeded, and it shards across four processes, so its wall reading (36-44s
observed on 2026-09-02) routinely runs past the shared 30s backstop with no
regression. The wall-accuses-cpu-acquits reading (`test_verify_budget_clock.py`)
cannot reach this case either: a sharding check's CPU reading is always higher
than its wall reading, so it can never acquit a check whose wall already
crossed a ceiling sized for a check with none of its own.

A check listed in `check_ceilings.owns_its_catastrophe` now answers to its own
named ceiling times `check_ceilings.catastrophic_factor`
(`budget.catastrophic_ceiling_for`) instead of the shared backstop. This does
not raise the named ceiling or the global backstop, and does not reduce the
debt a check owes against its own named ceiling.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovverify import budget  # noqa: E402

TABLE = budget.load()
NAMED_CHECK = "repository tooling tests"
NAMED_CEILING = float(TABLE["check_ceilings"]["named"][NAMED_CHECK])
GLOBAL_CEILING = float(TABLE["catastrophic_check_seconds"])
DERIVED_CEILING = budget.catastrophic_ceiling_for(NAMED_CHECK, TABLE)


class NamedCeilingOwnsItsCatastrophe(unittest.TestCase):
    """The three outcomes the derived ceiling must produce."""

    def test_the_check_is_declared_to_own_its_catastrophe(self) -> None:
        self.assertIn(NAMED_CHECK, TABLE["check_ceilings"]["owns_its_catastrophe"])

    def test_the_derived_ceiling_is_the_named_ceiling_times_the_factor(self) -> None:
        factor = float(TABLE["check_ceilings"]["catastrophic_factor"])
        self.assertEqual(DERIVED_CEILING, NAMED_CEILING * factor)

    def test_past_the_global_ceiling_but_under_its_own_raises_no_catastrophe(self) -> None:
        """The observed 2026-09-02 reading: 36-44s wall, well past 30.0s, under 60.0s."""
        wall = GLOBAL_CEILING + 10.0
        self.assertLess(wall, DERIVED_CEILING)
        debts, catastrophes = budget.judge([(NAMED_CHECK, wall)], TABLE)
        self.assertEqual(catastrophes, [])
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])

    def test_the_same_reading_still_appears_in_the_debt_table(self) -> None:
        wall = GLOBAL_CEILING + 10.0
        debts, _ = budget.judge([(NAMED_CHECK, wall)], TABLE)
        self.assertEqual(debts, [budget.Debt(NAMED_CHECK, wall, NAMED_CEILING)])

    def test_past_its_own_derived_ceiling_still_suspects_and_confirms(self) -> None:
        """A genuine blowout of this check, not host contention, remains blocking."""
        wall = DERIVED_CEILING + 5.0
        _, catastrophes = budget.judge([(NAMED_CHECK, wall)], TABLE)
        self.assertEqual(catastrophes,
                          [budget.Catastrophe(NAMED_CHECK, wall, DERIVED_CEILING)])
        # Pooled alone is only suspected; an isolated re-read past the same
        # derived ceiling is what confirms and refuses (catastrophic_confirm_alone).
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])
        confirmed = [c._replace(alone=wall) for c in catastrophes]
        self.assertEqual(budget.refusing(confirmed, TABLE), confirmed)

    def test_an_unnamed_check_still_suspects_and_confirms_past_the_global_number(self) -> None:
        """A check with no named ceiling is not swept into the wider allowance."""
        wall = GLOBAL_CEILING + 0.001
        _, catastrophes = budget.judge([("some new check nobody named", wall)], TABLE)
        self.assertEqual(catastrophes,
                          [budget.Catastrophe("some new check nobody named", wall,
                                               GLOBAL_CEILING)])
        self.assertEqual(budget.refusing(catastrophes, TABLE), [])
        confirmed = [c._replace(alone=wall) for c in catastrophes]
        self.assertEqual(budget.refusing(confirmed, TABLE), confirmed)

    def test_a_named_check_not_listed_still_answers_to_the_global_ceiling(self) -> None:
        """Owning a named ceiling does not by itself widen the catastrophic ceiling."""
        other = "Asset Service reference tests"
        self.assertNotIn(other, TABLE["check_ceilings"]["owns_its_catastrophe"])
        self.assertEqual(budget.catastrophic_ceiling_for(other, TABLE), GLOBAL_CEILING)


if __name__ == "__main__":
    unittest.main()
