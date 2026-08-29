"""Focused checks for decisions/0098 milestone-queued witnessing."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import authority  # noqa: E402


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class MilestoneWitnessCadence(unittest.TestCase):
    """Blue gates ordinary landing; independent witness gates witness claims."""

    def _landing_grant(self) -> dict:
        grants = _json("contracts/standing-grants.json")["grants"]
        return next(g for g in grants if g["grant_id"] == "grant:standing-landing-loop")

    def _request(self) -> dict:
        return {
            "request_schema": "soveraeign-authority-request/v1",
            "actor_id": "sov",
            "capability": "repository.land",
            "effect_class": "RESOURCE_CONSUMPTION",
            "at": datetime(2026, 9, 1, tzinfo=timezone.utc).isoformat(),
            "branch": "main",
            "paths": ["scripts/sov_land.py"],
            "spend": {"unit": "agent_invocations", "amount": 4},
            "evidence": {
                "checks": {"verify": "PASS", "lint": "PASS"},
                "observation": None,
            },
        }

    def test_ordinary_built_landing_does_not_require_witness(self):
        grant = self._landing_grant()
        self.assertFalse(grant["preconditions"]["requires_independent_observation"])
        result = authority.evaluate([grant], self._request())
        self.assertEqual(result["verdict"], authority.PERMITTED)

    def test_a_boundary_that_declares_witness_still_refuses_without_it(self):
        grant = deepcopy(self._landing_grant())
        grant["preconditions"]["requires_independent_observation"] = True
        result = authority.evaluate([grant], self._request())
        self.assertEqual(result["verdict"], authority.REFUSED)
        self.assertEqual(result["code"], authority.OBSERVATION_MISSING)

    def test_built_to_witnessed_still_requires_independent_receipts(self):
        table = _json("contracts/ticket-transitions.json")
        transition = next(
            t for t in table["transitions"]
            if t["from"] == "BUILT_SELF_TESTED_NOT_WITNESSED"
            and t["to"] == "WITNESSED"
        )
        self.assertTrue(transition["requires_distinct_actor"])
        self.assertTrue(transition["requires_purple"])
        self.assertEqual(
            set(transition["requires_evidence"]),
            {"witness_receipt", "purple_receipt"},
        )

    def test_capable_node_still_consumes_outside_observation(self):
        circuit = _json("contracts/work-circuit.json")
        capable = next(s for s in circuit["stages"] if s["stage"] == "CAPABLE_NODE")
        joined = " ".join(capable["admits_when"]).lower()
        self.assertIn("independent participant", joined)
        self.assertIn("observed", joined)

    def test_built_queue_action_is_continue_not_immediate_red(self):
        queue = _json("contracts/ticket-queue-policy.json")
        action = queue["next_action"]["BUILT_SELF_TESTED_NOT_WITNESSED"].lower()
        self.assertIn("continue reachable work", action)
        self.assertIn("verification-engagement", action)
        self.assertNotIn("run the red lane", action)


if __name__ == "__main__":
    unittest.main()
