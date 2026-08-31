"""Positive and defeating cases for the phase reading in SessionStart context."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsession import brief, phase_context  # noqa: E402
import sov_opening_readiness  # noqa: E402


class SessionPhaseContext(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "contracts").mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, status_phase: str, phases: list[dict], next_gate: str = "NEXT") -> None:
        (self.root / "STATUS.yaml").write_text(
            f"phase: {status_phase}\nnext_gate: {next_gate}\n", encoding="utf-8")
        (self.root / "contracts" / "phases.json").write_text(
            json.dumps({"phases": phases}) + "\n", encoding="utf-8")

    @staticmethod
    def phase(phase_id: str, execution: str, terminal: str = "IN_FLIGHT") -> dict:
        return {
            "phase_id": phase_id,
            "title": phase_id.upper(),
            "execution_status": execution,
            "acceptance_status": "NOT_EARNED",
            "terminal": terminal,
            "exit_clauses": [{"clause_id": "Q1", "text": "prove one circuit"}],
        }

    def test_none_active_agrees_with_a_closed_registry(self) -> None:
        self.write("NONE_ACTIVE", [self.phase("phase:i", "CLOSED", "CLOSED_INCOMPLETE")],
                   "SUCCESSOR_PHASE_OPENING")
        data = phase_context.collect(self.root)
        self.assertEqual(data["defects"], [])
        self.assertIsNone(data["active"])
        self.assertEqual(data["latest_terminal"]["phase_id"], "phase:i")
        rendered = "\n".join(phase_context.render(data))
        self.assertIn("phase: NONE_ACTIVE", rendered)
        self.assertIn("SUCCESSOR_PHASE_OPENING", rendered)
        self.assertIn("phase:i — CLOSED_INCOMPLETE", rendered)

    def test_one_open_phase_is_rendered_only_when_status_names_it(self) -> None:
        self.write("phase:one", [self.phase("phase:i", "CLOSED"),
                                 self.phase("phase:one", "OPEN")], "PHASE_TERMINAL")
        data = phase_context.collect(self.root)
        self.assertEqual(data["defects"], [])
        self.assertEqual(data["active"]["phase_id"], "phase:one")
        rendered = "\n".join(phase_context.render(data))
        self.assertIn("phase: phase:one — PHASE:ONE (OPEN)", rendered)
        self.assertIn("Q1: prove one circuit", rendered)

    def test_status_cannot_hide_an_open_phase(self) -> None:
        self.write("NONE_ACTIVE", [self.phase("phase:one", "OPEN")])
        data = phase_context.collect(self.root)
        self.assertIn("STATUS_NONE_ACTIVE_WITH_OPEN_PHASE", data["defects"])
        self.assertIn("CONFLICT", "\n".join(phase_context.render(data)))

    def test_status_cannot_invent_an_open_phase(self) -> None:
        self.write("phase:one", [self.phase("phase:i", "CLOSED")])
        data = phase_context.collect(self.root)
        self.assertIn("STATUS_PHASE_NOT_OPEN_IN_REGISTRY", data["defects"])

    def test_briefing_renders_registered_intent_and_phase_authority(self) -> None:
        data = {
            "session": "alpha", "intent": "close the recorder seam", "tree": "/repo",
            "branch": "feat/x", "position": "1 ahead of main, 0 behind",
            "shared_tree": [], "peers": [], "held": {}, "next_decision": 2,
            "principal": {
                "session": "alpha",
                "principal": "principal:alpha",
                "kind": "MODEL",
                "verification": "DECLARED",
                "controller": "principal:root",
                "hops": 1,
                "root": "principal:root",
                "basis": "test fixture",
                "defects": [],
                "registry": "contracts/principals.json",
            },
            "phase": {
                "status_phase": "NONE_ACTIVE", "next_gate": "SUCCESSOR_PHASE_OPENING",
                "active": None,
                "latest_terminal": self.phase("phase:i", "CLOSED", "CLOSED_INCOMPLETE"),
                "defects": [],
                "sources": [
                    {"path": "STATUS.yaml", "digest": "sha256:" + "a" * 64},
                    {"path": "contracts/phases.json", "digest": "sha256:" + "b" * 64},
                ],
            },
        }
        rendered = brief.render(data)
        self.assertIn("intent: close the recorder seam", rendered)
        self.assertIn("phase: NONE_ACTIVE", rendered)
        self.assertIn("phase authority: STATUS.yaml@aaaaaaaaaaaa", rendered)
        self.assertIn("discover what this node exposes", rendered)


class OpeningRehearsalContract(unittest.TestCase):
    def test_repository_reading_is_ready_or_already_active_without_hidden_defect(self):
        report = sov_opening_readiness.assess(ROOT)
        self.assertIn(report["state"], {"READY_TO_OPEN", "ACTIVE_PHASE"})
        self.assertEqual(report["defects"], [])
        self.assertFalse(report["authoritative"])


if __name__ == "__main__":
    unittest.main()
