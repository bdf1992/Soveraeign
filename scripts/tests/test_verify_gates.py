"""Structural cases for the dev/main gate partition in `scripts/verify.py`.

The main gate must stay exactly what a run executes today; the dev gate must be
a strict subset that never carries a check the partition rule names as
bookkeeping (a derived page, a counted claim, a receipt, a witness record, or
governing prose graded against the tree). A timing catastrophe must refuse
under the main gate and must not refuse under the dev gate.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch
import json
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402
from sovverify import budget, clocks  # noqa: E402
from sovverify.checks import CHECKS  # noqa: E402
from sovverify.shape import DEV_GATE, MAIN_GATE, Check  # noqa: E402

#: Named in the contract as failing today on stale bookkeeping rather than
#: wrong behaviour; the dev gate must exclude every one of them by name.
MAIN_ONLY_NAMES = {
    "orientation snapshot",
    "documentation reader",
    "operation surface page",
}


class GatePartition(unittest.TestCase):
    """The table's own `gate` field, read the same way `verify.py` reads it."""

    def test_every_check_answers_to_one_of_the_two_known_gates(self) -> None:
        self.assertTrue(all(check.gate in (DEV_GATE, MAIN_GATE) for check in CHECKS))

    def test_dev_gate_is_a_strict_subset_of_main(self) -> None:
        # --gate main runs CHECKS unfiltered (verify.main), so "main" here is
        # every name the table holds, not only entries tagged gate=MAIN_GATE.
        dev_names = {check.name for check in CHECKS if check.gate == DEV_GATE}
        all_names = {check.name for check in CHECKS}
        self.assertTrue(dev_names)
        self.assertTrue(dev_names < all_names)

    def test_dev_gate_excludes_every_named_main_only_check(self) -> None:
        all_names = {check.name for check in CHECKS}
        dev_names = {check.name for check in CHECKS if check.gate == DEV_GATE}
        self.assertTrue(MAIN_ONLY_NAMES.issubset(all_names))
        self.assertFalse(dev_names & MAIN_ONLY_NAMES)


def _instant(check: Check) -> tuple[Check, clocks.Reading]:
    """Stand in for `run_check`: no subprocess, always clean, always instant."""
    return check, clocks.Reading(0, "", 0.0, 0.0, "posix-wait4-rusage")


class GateSelection(unittest.TestCase):
    """`verify.main` actually restricts the run to the checks a gate names.

    `run_check` is faked so this proves selection, not the checks themselves;
    `ThreadPoolExecutor.map` guarantees its results follow the input order
    regardless of thread scheduling, so the observed order in the written
    records is the order the gate selected, not an artifact of timing.
    """

    def _subjects(self, argv: list[str]) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "observe.json"
            with patch.object(verify, "run_check", side_effect=_instant):
                verify.main([*argv, "--observe", str(out)], run_id="r",
                           now="2026-09-02T00:00:00Z")
            records = json.loads(out.read_bytes().decode("utf-8"))
        return [record["subject"] for record in records]

    def test_gate_main_runs_the_same_checks_in_the_same_order_as_today(self) -> None:
        self.assertEqual(self._subjects(["--gate", MAIN_GATE]),
                         [check.name for check in CHECKS])

    def test_gate_dev_runs_only_the_dev_named_checks_in_table_order(self) -> None:
        self.assertEqual(self._subjects(["--gate", DEV_GATE]),
                         [check.name for check in CHECKS if check.gate == DEV_GATE])

    def test_default_gate_is_main(self) -> None:
        self.assertEqual(self._subjects([]), [check.name for check in CHECKS])


class CatastropheRefusal(unittest.TestCase):
    """A timing catastrophe refuses the main gate and never refuses the dev gate."""

    def _fake_table(self) -> dict:
        table = budget.load()
        table = dict(table)
        table["catastrophic_check_seconds"] = 0.0
        table["catastrophic_confirm_alone"] = False
        return table

    def test_a_catastrophic_check_refuses_under_main_and_not_under_dev(self) -> None:
        dev_check = next(check for check in CHECKS if check.gate == DEV_GATE)
        subset = (Check(dev_check.name, dev_check.command, dev_check.cwd, dev_check.relation,
                        dev_check.observes, gate=DEV_GATE),)
        fake_reading = clocks.Reading(0, "slow", 999.0, 999.0, "posix-wait4-rusage")

        with patch.object(verify, "CHECKS", subset), \
             patch.object(verify, "BUDGET_TABLE", self._fake_table()), \
             patch.object(verify, "run_check", return_value=(subset[0], fake_reading)):
            main_exit = verify.main(["--gate", MAIN_GATE], run_id="r",
                                    now="2026-09-02T00:00:00Z")
            dev_exit = verify.main(["--gate", DEV_GATE], run_id="r",
                                   now="2026-09-02T00:00:00Z")

        self.assertEqual(main_exit, 1)
        self.assertEqual(dev_exit, 0)


if __name__ == "__main__":
    unittest.main()
