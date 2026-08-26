"""Tests for the landing gate's path handling and its refusal to stage blindly.

The gate grades a landing request against `contracts/standing-grants.json`, and a
grant declares repository-relative prefixes. What a worker hands back is not
guaranteed to be in that form. The first `sov-loop` run reported absolute Windows
paths, which would have failed every scope check for the wrong reason, so the
conversion has a test rather than a comment.
"""

from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_land  # noqa: E402
from sovkernel import authority  # noqa: E402


class RepoRelative(unittest.TestCase):
    """A path reaches the scope check in the form the grant's prefixes are written."""

    def test_an_absolute_path_under_the_root_becomes_relative(self):
        absolute = str(ROOT / "scripts" / "sov_land.py")
        self.assertEqual(sov_land.repo_relative(absolute), "scripts/sov_land.py")

    def test_a_relative_path_keeps_its_meaning_and_loses_its_backslashes(self):
        self.assertEqual(sov_land.repo_relative(r"scripts\tests\test_sov_land.py"),
                         "scripts/tests/test_sov_land.py")

    def test_a_dot_dot_segment_does_not_survive_into_the_comparison(self):
        """A relative path is not automatically inside the repository.

        `scripts/../STATUS.yaml` begins with an admitted prefix and names an
        excluded file. Resolving it first is the whole reason the exclusion list
        means anything.
        """
        self.assertEqual(sov_land.repo_relative("scripts/../STATUS.yaml"), "STATUS.yaml")
        self.assertEqual(sov_land.repo_relative("scripts/../decisions/0001-x.md"),
                         "decisions/0001-x.md")

    def test_a_relative_path_can_leave_the_repository_and_is_not_pulled_back_in(self):
        converted = sov_land.repo_relative("scripts/../../elsewhere/x.py")
        self.assertTrue(Path(converted).is_absolute())
        self.assertNotIn("..", converted)

    def test_an_absolute_path_that_escapes_is_reported_resolved(self):
        """A refusal that misnames the file is a refusal a reader cannot check."""
        escaping = str(ROOT / "scripts" / ".." / ".." / "elsewhere" / "x.py")
        converted = sov_land.repo_relative(escaping)
        self.assertNotIn("..", converted)
        self.assertTrue(Path(converted).is_absolute())

    def test_a_path_outside_the_repository_is_not_rewritten_into_scope(self):
        """The defeating case: conversion must not become a way into the grant.

        A path the repository does not contain has no repository-relative form.
        Returning it unchanged is what keeps it failing the scope check; silently
        stripping it to a tail like `scripts/x.py` would admit a file the grant
        never covered.
        """
        outside = Path(ROOT.anchor) / "elsewhere" / "scripts" / "x.py"
        converted = sov_land.repo_relative(str(outside))
        self.assertNotEqual(converted, "scripts/x.py")
        self.assertTrue(Path(converted).is_absolute())


class ScopeAfterConversion(unittest.TestCase):
    """The conversion is only useful if the evaluator then reaches the right verdict."""

    GRANT = {
        "status": "RATIFIED",
        "grant_id": "grant:test",
        "issuer_id": "bdo",
        "actor_id": "sov",
        "authority_type": "VERIFICATION",
        "capabilities": ["repository.land"],
        "scope": {"paths": ["scripts/"], "excluded_paths": [], "branches": ["main"]},
        "budget": {"unit": "agent_invocations", "ceiling": 60},
        "preconditions": {},
        "effect_ceiling": "RECORD_LOCAL",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_until": "2099-01-01T00:00:00Z",
        "revoked_at": None,
    }

    def _request(self, raw_path: str) -> dict:
        return {
            "actor_id": "sov",
            "capability": "repository.land",
            "effect_class": "RECORD_LOCAL",
            "at": "2026-09-01T12:00:00Z",
            "branch": "main",
            "paths": [sov_land.repo_relative(raw_path)],
            "evidence": {"checks": {}},
        }

    def test_an_absolute_in_repository_path_is_admitted_once_converted(self):
        result = authority.evaluate([self.GRANT],
                                    self._request(str(ROOT / "scripts" / "sov_land.py")))
        self.assertEqual(result["verdict"], authority.PERMITTED)

    def test_the_same_path_is_refused_when_it_reaches_the_gate_unconverted(self):
        """Proves the repair is load-bearing, not decorative."""
        request = self._request("scripts/sov_land.py")
        request["paths"] = [str(ROOT / "scripts" / "sov_land.py")]
        result = authority.evaluate([self.GRANT], request)
        self.assertEqual(result["verdict"], authority.REFUSED)
        self.assertEqual(result["code"], authority.AUTHORITY_REFUSED)

    def test_dot_dot_cannot_walk_out_of_the_grants_own_exclusions(self):
        """The escape a witness found on 2026-08-25, graded against the real grant.

        Each of these begins with an admitted prefix and names something the
        standing grant excludes precisely so an exercise of it cannot touch
        standing or widen itself.
        """
        excluded = {"paths": ["scripts/"],
                    "excluded_paths": ["decisions/", "STATUS.yaml",
                                       "contracts/standing-grants.json"],
                    "branches": ["main"]}
        grant = {**self.GRANT, "scope": excluded}
        for escape in ("scripts/../STATUS.yaml",
                       "scripts/../decisions/0061-x.md",
                       "scripts/../contracts/standing-grants.json",
                       "scripts/../../elsewhere/x.py"):
            with self.subTest(escape=escape):
                result = authority.evaluate([grant], self._request(escape))
                self.assertEqual(result["verdict"], authority.REFUSED, escape)
                self.assertEqual(result["code"], authority.AUTHORITY_REFUSED)

    def test_a_path_outside_the_repository_stays_refused_after_conversion(self):
        outside = Path(ROOT.anchor) / "elsewhere" / "scripts" / "x.py"
        result = authority.evaluate([self.GRANT], self._request(str(outside)))
        self.assertEqual(result["verdict"], authority.REFUSED)
        self.assertEqual(result["code"], authority.AUTHORITY_REFUSED)


class LandRefusesABlanketStage(unittest.TestCase):
    """Sessions here share one working directory; the gate never stages what it was not given."""

    def test_land_without_explicit_paths_is_refused(self):
        self.assertEqual(sov_land.main(["land"]), 2)


if __name__ == "__main__":
    unittest.main()
