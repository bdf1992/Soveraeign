from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import authority  # noqa: E402


class CapabilitySpecificPreconditions(unittest.TestCase):
    def grant(self):
        return {
            "status": "RATIFIED",
            "grant_id": "grant:test",
            "issuer_id": "bdo",
            "actor_id": "sov",
            "authority_type": "VERIFICATION",
            "capabilities": ["repository.commit", "repository.land"],
            "scope": {"paths": ["scripts/"], "excluded_paths": [], "branches": ["main"]},
            "budget": {"unit": "agent_invocations", "ceiling": 60},
            "preconditions_by_capability": {
                "repository.commit": {"required_checks": ["verify", "lint"]},
                "repository.land": {
                    "required_checks": ["verify", "lint"],
                    "requires_independent_observation": True,
                },
            },
            "effect_ceiling": "RESOURCE_CONSUMPTION",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_until": "2099-01-01T00:00:00Z",
            "revoked_at": None,
        }

    def request(self, capability, observation=None):
        return {
            "actor_id": "sov",
            "capability": capability,
            "effect_class": "RESOURCE_CONSUMPTION",
            "at": "2026-09-01T12:00:00Z",
            "branch": "main",
            "paths": ["scripts/x.py"],
            "spend": {"unit": "agent_invocations", "amount": 1},
            "evidence": {
                "checks": {"verify": "PASS", "lint": "PASS"},
                "observation": observation,
            },
        }

    def test_commit_can_freeze_before_independent_observation(self):
        result = authority.evaluate([self.grant()], self.request("repository.commit"))
        self.assertEqual(result["verdict"], authority.PERMITTED)

    def test_land_still_requires_independent_observation(self):
        result = authority.evaluate([self.grant()], self.request("repository.land"))
        self.assertEqual(result["code"], authority.OBSERVATION_MISSING)

    def test_land_accepts_confirmed_independent_observation(self):
        observation = {
            "observer_id": "witness-1",
            "contributed_to_build": False,
            "verdict": "CONFIRMED",
        }
        result = authority.evaluate(
            [self.grant()], self.request("repository.land", observation)
        )
        self.assertEqual(result["verdict"], authority.PERMITTED)


if __name__ == "__main__":
    unittest.main()
