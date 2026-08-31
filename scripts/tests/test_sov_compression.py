"""Defeating and positive cases for the daily/weekly compression reader."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import sov_compression as compression  # noqa: E402


class PhaseReading(unittest.TestCase):
    def test_none_active_is_the_gap_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "STATUS.yaml").write_text(
                "phase: NONE_ACTIVE\nnext_gate: SUCCESSOR_PHASE_OPENING\n",
                encoding="utf-8",
            )
            self.assertEqual(
                {
                    "phase": "NONE_ACTIVE",
                    "next_gate": "SUCCESSOR_PHASE_OPENING",
                    "gap_preserved": True,
                },
                compression.phase_reading(root),
            )

    def test_an_active_phase_is_not_reported_as_gap_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "STATUS.yaml").write_text(
                "phase: SOME_SUCCESSOR\nnext_gate: SOMETHING\n", encoding="utf-8",
            )
            self.assertFalse(compression.phase_reading(root)["gap_preserved"])

    def test_comments_do_not_become_status_fields(self):
        values = compression._status_values(
            "# phase: PHASE_I\nphase: NONE_ACTIVE\n# next_gate: WRONG\n"
        )
        self.assertEqual("NONE_ACTIVE", values["phase"])
        self.assertNotIn("next_gate", values)


class PathClassification(unittest.TestCase):
    def test_governing_documents_stay_distinct_from_projections(self):
        self.assertEqual("governance", compression.classify_path("STATUS.yaml"))
        self.assertEqual("projection", compression.classify_path("docs/documentation.html"))

    def test_harness_and_service_are_separate_readings(self):
        self.assertEqual("harness", compression.classify_path("scripts/verify.py"))
        self.assertEqual("services", compression.classify_path("services/record/src/core.py"))

    def test_unknown_paths_are_not_force_fit(self):
        self.assertEqual("other", compression.classify_path("some-new-root/data.bin"))


class ChurnSummary(unittest.TestCase):
    def test_one_path_touched_by_two_commits_is_one_subject_with_two_observations(self):
        result = compression.summarize_commits([
            ("a", ["STATUS.yaml", "scripts/verify.py"]),
            ("b", ["STATUS.yaml"]),
        ])
        self.assertEqual(2, result["commits"])
        self.assertEqual(2, result["unique_paths"])
        self.assertEqual(
            {"path": "STATUS.yaml", "commits_touched": 2},
            result["top_churn"][0],
        )

    def test_duplicate_names_inside_one_commit_do_not_inflate_churn(self):
        result = compression.summarize_commits([
            ("a", ["STATUS.yaml", "STATUS.yaml", "STATUS.yaml"]),
        ])
        self.assertEqual(1, result["top_churn"][0]["commits_touched"])

    def test_category_touches_are_observations_not_standing(self):
        result = compression.summarize_commits([
            ("a", ["STATUS.yaml", "docs/documentation.html", "services/record/a.py"]),
        ])
        self.assertEqual(
            {"governance": 1, "projection": 1, "services": 1},
            result["category_touches"],
        )


class InstrumentBoundary(unittest.TestCase):
    def test_daily_and_weekly_are_one_instrument_with_different_windows(self):
        self.assertEqual(24, compression.WINDOW_HOURS["daily"])
        self.assertEqual(168, compression.WINDOW_HOURS["weekly"])

    def test_the_reader_declares_observation_only(self):
        phase = {"phase": "NONE_ACTIVE", "next_gate": "SUCCESSOR_PHASE_OPENING",
                 "gap_preserved": True}
        lessons = {"entries": 1, "standings": {"RECORDED": 1},
                   "drain": {"recorded": 1, "threshold": 7, "due": False,
                             "refuses": False},
                   "defects": [], "claims_clean": True}
        refs = {"observed_refs": ["main"], "non_main_refs": []}
        with (
            patch.object(compression, "_git", return_value="abc123\n"),
            patch.object(compression, "_commit_paths", return_value=[]),
            patch.object(compression, "phase_reading", return_value=phase),
            patch.object(compression, "lessons_reading", return_value=lessons),
            patch.object(compression, "local_refs", return_value=refs),
        ):
            result = compression.reading("daily", Path("/not-read"))
        self.assertEqual("NONE_OBSERVATION_ONLY", result["authority"])
        self.assertEqual("abc123", result["subject_revision"])
        self.assertEqual(phase, result["phase"])

    def test_an_unknown_mode_is_refused_before_reading(self):
        with self.assertRaises(ValueError):
            compression.reading("monthly", Path("/not-read"))


if __name__ == "__main__":
    unittest.main()
