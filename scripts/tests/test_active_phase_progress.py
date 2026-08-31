"""Active campaigns must initialize and preserve an exit-custody progress floor."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

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


if __name__ == "__main__":
    unittest.main()
