"""Defeating checks for the prepared commissioning evidence workflow."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".claude/workflows/sov-loop.js"


class FindingContract(unittest.TestCase):
    def test_workflow_names_every_required_finding_field(self) -> None:
        schema = json.loads((ROOT / "contracts/finding.schema.json").read_text(encoding="utf-8"))
        text = WORKFLOW.read_text(encoding="utf-8")
        for field in schema["required"]:
            self.assertIn(field, text, field)

    def test_missing_projection_is_envelope_not_fake_finding(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("const REVIEW_RESULT", text)
        self.assertIn("status: 'UNATTESTABLE'", text)
        self.assertIn("BAD_PROJECTION_IDS = ['NONE', 'UNAVAILABLE', 'MISSING']", text)
        self.assertNotIn("record_projection_id NONE", text)
        self.assertNotIn("record_projection_id: 'NONE'", text)
        self.assertNotIn("record_projection_id: \"NONE\"", text)

    def test_comparison_requires_two_real_frozen_findings(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("haveParticipantFinding && haveWorkFinding", text)
        self.assertIn("classifications: ['RECORD_DEFECT']", text)
        self.assertIn("comparison envelope is not itself a Finding", text)
        self.assertIn("input_finding_ids", text)

    def test_evidence_landing_requires_confirmed_findings_and_observation(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("evidenceReviewsConfirmed", text)
        self.assertIn("claimsConfirmed(orchestrationReview)", text)
        self.assertIn("claimsConfirmed(witnessed)", text)
        self.assertIn("!!witnessed.observation_file", text)
        self.assertIn("const observationArg = witnessed.observation_file", text)
        self.assertNotIn("witnessed.observation_file || 'MISSING'", text)


class RoleContracts(unittest.TestCase):
    def test_orchestrator_refuses_placeholder_finding(self) -> None:
        text = (ROOT / ".claude/agents/sov-orchestrator.md").read_text(encoding="utf-8")
        self.assertIn("without a", text)
        self.assertIn("`Finding` object", text)
        self.assertIn("invented ids", text)

    def test_witness_freezes_before_observation_write(self) -> None:
        text = (ROOT / ".claude/agents/sov-witness.md").read_text(encoding="utf-8")
        self.assertIn("Freeze a real Finding", text)
        self.assertIn("before you emit your observation record", text)
        self.assertIn("reports/observations/*.json", text)

    def test_controller_does_not_promote_missing_basis(self) -> None:
        text = (ROOT / ".claude/agents/sov-controller.md").read_text(encoding="utf-8")
        self.assertIn("RECORD_DEFECT", text)
        self.assertIn("never manufacture a placeholder", text)
        self.assertIn("non-authoritative comparison envelope", text)


if __name__ == "__main__":
    unittest.main()
