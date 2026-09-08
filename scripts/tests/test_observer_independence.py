"""Prove the landing gate measures what it can about an observer, and names what it cannot.

The gate required `contributed_to_build: false`, a boolean the observer sets about itself.
Reading it and nothing else grades a declaration where a measurement was available, which
is the defect this repository keeps finding in its own checks - and it sat in the gate that
decides whether work reaches `main`.

Three things are measurable from the landing request alone and are now measured: an
observation naming no observer, an observer that is the actor exercising the grant, and an
observation file among the paths being landed. Everything past that is still the
observer's word, so the ledger records which of the two it was rather than recording them
identically.

Nothing here reads the session registry. That store is per-machine and gitignored, so a
check joining on it would pass wherever it is absent, which is a skipped check satisfying
its own requirement (`CLAUDE.md`, trap T5). Passing establishes `BUILT`.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel import authority  # noqa: E402

GRANT = {
    "grant_schema": "soveraeign-authority-grant/v1",
    "status": "RATIFIED",
    "grant_id": "grant:test",
    "issuer_id": "bdo",
    "actor_id": "sov",
    "authority_type": "VERIFICATION",
    "capabilities": ["repository.land"],
    "scope": {"paths": ["scripts/"], "excluded_paths": [], "branches": ["main"]},
    "budget": {"unit": "agent_invocations", "ceiling": 60},
    "preconditions_by_capability": {
        "repository.land": {"required_checks": ["verify", "lint"],
                            "requires_independent_observation": True},
    },
    "effect_ceiling": "RESOURCE_CONSUMPTION",
    "valid_from": "2026-01-01T00:00:00Z",
    "valid_until": "2099-01-01T00:00:00Z",
    "revoked_at": None,
}


def request(observation: dict | None, paths: list[str] | None = None) -> dict:
    return {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": "sov",
        "capability": "repository.land",
        "effect_class": "RESOURCE_CONSUMPTION",
        "at": "2026-09-08T00:00:00Z",
        "branch": "main",
        "paths": paths if paths is not None else ["scripts/thing.py"],
        "spend": {"unit": "agent_invocations", "amount": 3},
        "evidence": {"checks": {"verify": "PASS", "lint": "PASS"},
                     "observation": observation},
    }


CLEAN = {"observer_id": "witness:governance", "verdict": "CONFIRMED",
         "contributed_to_build": False,
         "observation_file": "reports/observations/2026-09-08-thing.json"}


class TheGateMeasuresWhatItCan(unittest.TestCase):
    def verdict(self, observation, paths=None):
        return authority._observation_verdict(GRANT, request(observation, paths))

    def test_an_independent_observation_passes(self):
        """Without this the refusals below could all come from a gate that refuses all."""
        self.assertIsNone(self.verdict(CLEAN))

    def test_an_observation_naming_no_observer_is_refused(self):
        """Nothing about independence can be established from an anonymous reading, and an
        absent name used to satisfy the check as readily as a real one."""
        for empty in ({**CLEAN, "observer_id": ""}, {**CLEAN, "observer_id": "   "},
                      {k: v for k, v in CLEAN.items() if k != "observer_id"}):
            with self.subTest(observation=empty):
                reason, _ = self.verdict(empty)
                self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_the_actor_exercising_the_grant_cannot_be_its_own_observer(self):
        reason, detail = self.verdict({**CLEAN, "observer_id": "sov"})
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)
        self.assertIn("cannot", detail)

    def test_an_observation_among_the_landed_paths_is_inside_the_change(self):
        """Measured, not declared: the observation is in the set of paths being landed."""
        reason, _ = self.verdict(
            CLEAN, ["scripts/thing.py", "reports/observations/2026-09-08-thing.json"])
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_an_observation_outside_the_landed_paths_is_not_refused_for_that(self):
        self.assertIsNone(self.verdict(CLEAN, ["scripts/thing.py"]))

    def test_the_declared_boolean_still_refuses(self):
        """The declaration is weaker evidence, not no evidence; it still refuses."""
        reason, _ = self.verdict({**CLEAN, "contributed_to_build": True})
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_a_dissenting_observation_is_not_a_landing(self):
        reason, _ = self.verdict({**CLEAN, "verdict": "DISSENTED"})
        self.assertEqual(reason, authority.OBSERVATION_MISSING)


class TheBasisIsRecordedRatherThanBlurred(unittest.TestCase):
    def test_a_reading_resting_on_the_observers_word_says_so(self):
        self.assertEqual(authority.independence_basis(request(CLEAN)), "DECLARED_ONLY")

    def test_a_structurally_readable_observer_is_measured(self):
        """When the observer names a path the request carries, the relation is readable
        from the request rather than taken on trust."""
        observation = {**CLEAN, "observer_id": "scripts/thing.py"}
        self.assertEqual(authority.independence_basis(request(observation)), "MEASURED")

    def test_the_basis_never_silently_claims_more_than_it_read(self):
        """The point of the field: an unmeasurable reading must not record as measured."""
        self.assertEqual(
            authority.independence_basis(request(CLEAN, paths=[])), "DECLARED_ONLY")


if __name__ == "__main__":
    unittest.main()
