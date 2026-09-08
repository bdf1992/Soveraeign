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


def request(observation: dict | None, paths: list[str] | None = None,
            observation_path: str | None = None, observation_resolved: bool = False) -> dict:
    return {
        "request_schema": "soveraeign-authority-request/v1",
        "actor_id": "sov",
        "capability": "repository.land",
        "effect_class": "RESOURCE_CONSUMPTION",
        "at": "2026-09-08T00:00:00Z",
        "branch": "main",
        "paths": paths if paths is not None else ["scripts/thing.py"],
        "observation_path": observation_path,
        "observation_resolved": observation_resolved,
        "spend": {"unit": "agent_invocations", "amount": 3},
        "evidence": {"checks": {"verify": "PASS", "lint": "PASS"},
                     "observation": observation},
    }


CLEAN = {"observer_id": "witness:governance", "verdict": "CONFIRMED",
         "contributed_to_build": False}
WRITTEN = "reports/observations/2026-09-08-thing.json"


class TheGateMeasuresWhatItCan(unittest.TestCase):
    def verdict(self, observation, paths=None, observation_path=None):
        return authority._observation_verdict(
            GRANT, request(observation, paths, observation_path))

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
        """Measured, not declared: the path comes from the landing tool, not the observer."""
        reason, _ = self.verdict(CLEAN, ["scripts/thing.py", WRITTEN], WRITTEN)
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_a_landed_directory_containing_the_observation_is_inside_the_change(self):
        """Landing the directory lands the file in it."""
        reason, _ = self.verdict(CLEAN, ["reports/observations"], WRITTEN)
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_an_observation_outside_the_landed_paths_is_not_refused_for_that(self):
        self.assertIsNone(self.verdict(CLEAN, ["scripts/thing.py"], WRITTEN))

    def test_a_path_merely_ending_in_the_same_name_is_not_a_match(self):
        """An unanchored suffix match refused a landing over a file it never touched:
        docs/release-notes.json read as covering notes.json."""
        self.assertIsNone(self.verdict(CLEAN, ["docs/release-notes.json"], "notes.json"))

    def test_the_spelling_of_a_path_does_not_decide_the_answer(self):
        reason, _ = self.verdict(CLEAN, ["./reports/observations/"], WRITTEN)
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_the_declared_boolean_still_refuses(self):
        """The declaration is weaker evidence, not no evidence; it still refuses."""
        reason, _ = self.verdict({**CLEAN, "contributed_to_build": True})
        self.assertEqual(reason, authority.OBSERVER_NOT_INDEPENDENT)

    def test_a_dissenting_observation_is_not_a_landing(self):
        reason, _ = self.verdict({**CLEAN, "verdict": "DISSENTED"})
        self.assertEqual(reason, authority.OBSERVATION_MISSING)


class TheBasisIsRecordedRatherThanBlurred(unittest.TestCase):
    def test_a_reading_resting_on_the_observers_word_says_so(self):
        """No observation path on the request: the relation was never read."""
        self.assertEqual(authority.observation_basis(request(CLEAN)), "DECLARED_ONLY")

    def test_a_request_carrying_the_observations_path_is_measured(self):
        """The landing tool knows where the observation lives, so the relation is read
        rather than taken on trust. An earlier form reached MEASURED only when the
        observer was named after a file, which no participant is."""
        self.assertEqual(
            authority.observation_basis(
                request(CLEAN, observation_path=WRITTEN, observation_resolved=True)),
            "SUPPLIED_AND_RESOLVED")

    def test_measured_is_reachable_by_an_ordinarily_named_observer(self):
        """The defect this replaced: MEASURED was unreachable in practice."""
        ordinary = {**CLEAN, "observer_id": "witness:governance"}
        self.assertEqual(
            authority.observation_basis(
                request(ordinary, observation_path=WRITTEN, observation_resolved=True)),
            "SUPPLIED_AND_RESOLVED")

    def test_a_path_the_caller_did_not_resolve_is_not_measured(self):
        """The defeating case for the repair above.

        An independent reading obtained MEASURED for `observation_path: "."` and for a
        path naming no file, because a non-empty string was taken as evidence that a
        comparison had something to compare. `authority.py` reads no files by design, so
        the caller that read the observation asserts it; without the assertion the reading
        rests on the observer's word and says so.
        """
        for path in (".", "not/a/file/at/all.json", WRITTEN):
            self.assertEqual(
                authority.observation_basis(request(CLEAN, observation_path=path)),
                "DECLARED_ONLY", f"{path!r} was reported as measured without resolution")

    def test_a_request_with_no_observation_at_all_is_not_measured(self):
        self.assertEqual(authority.observation_basis(request(None)), "DECLARED_ONLY")


if __name__ == "__main__":
    unittest.main()
