"""Active campaigns must initialize and preserve an exit-custody progress floor."""

from __future__ import annotations

from pathlib import Path
from unittest import mock
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_active_phase_progress as active  # noqa: E402
import sov_phase_progress as progress  # noqa: E402


def phase() -> dict:
    return {
        "phase_id": "phase:1-5",
        "exit_clauses": [
            {"clause_id": "P15-X1", "verdict": "NOT_EARNED",
             "held_by": "custody:phase-1-5/fresh-participation"},
        ],
    }


def custody(stage: str = "VERTICAL_SLICE") -> dict:
    return {
        "custody_id": "custody:phase-1-5/fresh-participation",
        "phase": "phase:1-5",
        "entry_stage": "ROOT_POINT",
        "target_stage": "CAPABLE_NODE",
        "members": [{"address": "work:fresh", "stage": stage}],
    }


def profile(floor: str = "ROOT_POINT") -> dict:
    return {
        "initialized_by": "seat:root",
        "initialized_on": "2026-08-31",
        "exit_custody_floors": {
            "custody:phase-1-5/fresh-participation": floor,
        },
    }


def codes(defects: list[dict]) -> set[str]:
    return {item["code"] for item in defects}


class ActivePhaseFloor(unittest.TestCase):
    def test_active_phase_without_initialized_profile_refuses(self) -> None:
        defects = progress.grade_active_phase("phase:1-5", phase(), None, [custody()])
        self.assertIn("ACTIVE_PHASE_PROGRESS_UNINITIALIZED", codes(defects))

    def test_every_unearned_exit_must_have_live_custody(self) -> None:
        defects = progress.grade_active_phase("phase:1-5", phase(), profile(), [])
        self.assertIn("MISSING_EXIT_CUSTODY", codes(defects))

    def test_every_exit_custody_must_be_in_the_floor(self) -> None:
        declared = profile()
        declared["exit_custody_floors"] = {}
        defects = progress.grade_active_phase("phase:1-5", phase(), declared, [custody()])
        self.assertIn("EXIT_CUSTODY_UNTRACKED", codes(defects))

    def test_custody_cannot_fall_below_its_opening_floor(self) -> None:
        defects = progress.grade_active_phase(
            "phase:1-5", phase(), profile("HORIZONTAL_SURFACE"), [custody("VERTICAL_SLICE")])
        self.assertIn("CUSTODY_STAGE_REGRESSION", codes(defects))

    def test_progress_above_floor_is_admissible(self) -> None:
        defects = progress.grade_active_phase(
            "phase:1-5", phase(), profile("ROOT_POINT"), [custody("VERTICAL_SLICE")])
        self.assertEqual(defects, [])

    def test_floor_for_non_exit_custody_refuses_as_stale_tracking(self) -> None:
        declared = profile()
        declared["exit_custody_floors"]["custody:phase-1-5/not-an-exit"] = "ROOT_POINT"
        defects = progress.grade_active_phase("phase:1-5", phase(), declared, [custody()])
        self.assertIn("EXIT_CUSTODY_UNTRACKED", codes(defects))


class TheReaderCanBeRun(unittest.TestCase):
    """The reader a fresh participant is told to run must say something.

    It held only functions until 2026-09-07, so running it printed nothing and
    exited 0 while CLAUDE.md and decisions/0102 both named it as the thing that
    grades the active phase. Eight witness passes recorded the silence -- six in
    witness/fresh-participation.md, two in witness/discovery-and-reuse.md -- and
    none could refuse it: a module with no entry point has no behaviour to defeat.
    These cases are that behaviour.
    """

    PHASE = {
        "phase_id": "phase:test",
        "title": "A Test Phase",
        "exit_clauses": [
            {"clause_id": "T-X1", "verdict": "NOT_EARNED", "held_by": "custody:test/carried"},
            {"clause_id": "T-X2", "verdict": "NOT_EARNED", "held_by": "custody:test/empty"},
        ],
    }
    RECORDS = [
        {"custody_id": "custody:test/carried", "entry_stage": "ROOT_POINT",
         "members": [{"address": "scripts/thing.py", "stage": "VERTICAL_SLICE"}]},
        {"custody_id": "custody:test/empty", "entry_stage": "ROOT_POINT", "members": []},
    ]
    PROFILE = {"exit_custody_floors": {"custody:test/carried": "ROOT_POINT",
                                       "custody:test/empty": "ROOT_POINT"}}

    def test_an_empty_reading_refuses_rather_than_exiting_zero(self) -> None:
        """The defect's shape, not its spelling.

        This replaced a case that asserted the source text contains
        `if __name__ == "__main__":`. A witness defeated that one by putting the
        literal in a comment: it passed against a module that printed nothing and
        exited 0, which is the exact original defect. It read a declaration where
        it could measure. Silence is now a refusal, so the behaviour is testable.
        """
        with mock.patch.object(active, "report", return_value=["", "   "]):
            code = active.main([])
        self.assertEqual(code, 1)

    def test_running_it_against_the_live_repository_prints_and_names_the_phase(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/sov_active_phase_progress.py"],
            cwd=str(ROOT), capture_output=True, text=True, check=False,
        )
        self.assertTrue(result.stdout.strip(), "the reader must not be silent")
        self.assertIn(active.status_phase(), result.stdout)

    def test_every_exit_clause_appears_in_the_reading(self) -> None:
        lines = "\n".join(active.report("phase:test", self.PHASE, self.PROFILE, self.RECORDS))
        self.assertIn("T-X1", lines)
        self.assertIn("T-X2", lines)

    def test_a_clause_whose_custody_carries_nothing_is_named(self) -> None:
        lines = "\n".join(active.report("phase:test", self.PHASE, self.PROFILE, self.RECORDS))
        self.assertIn("NO MEMBER", lines)
        self.assertIn("T-X2 (empty)", lines)

    def test_a_clause_whose_custody_carries_work_is_not_named_as_empty(self) -> None:
        """The defeat of the case above: a carried clause must not read as abandoned."""
        lines = "\n".join(active.report("phase:test", self.PHASE, self.PROFILE, self.RECORDS))
        self.assertNotIn("T-X1 (carried)", lines)
        self.assertIn("1 member(s)", lines)

    def test_no_active_phase_reads_as_no_active_phase_and_not_as_a_defect(self) -> None:
        lines = "\n".join(active.report("NONE_ACTIVE", None, None, []))
        self.assertIn("no active successor phase", lines)

    def test_a_phase_active_in_status_but_absent_from_the_registry_says_so(self) -> None:
        lines = "\n".join(active.report("phase:ghost", None, None, []))
        self.assertIn("absent from contracts/phases.json", lines)


if __name__ == "__main__":
    unittest.main()
