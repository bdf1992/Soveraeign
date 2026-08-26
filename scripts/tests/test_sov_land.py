"""Tests for the landing gate's path handling and its refusal to stage blindly.

The gate grades a landing request against `contracts/standing-grants.json`, and a
grant declares repository-relative prefixes. What a worker hands back is not
guaranteed to be in that form. The first `sov-loop` run reported absolute Windows
paths, which would have failed every scope check for the wrong reason, so the
conversion has a test rather than a comment.
"""

from __future__ import annotations

from pathlib import Path
from unittest import mock
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_land  # noqa: E402
from sovland import tree  # noqa: E402
from sovkernel import authority  # noqa: E402


class RepoRelative(unittest.TestCase):
    """A path reaches the scope check in the form the grant's prefixes are written."""

    def test_an_absolute_path_under_the_root_becomes_relative(self):
        absolute = str(ROOT / "scripts" / "sov_land.py")
        self.assertEqual(tree.repo_relative(absolute), "scripts/sov_land.py")

    def test_a_relative_path_keeps_its_meaning_and_loses_its_backslashes(self):
        self.assertEqual(tree.repo_relative(r"scripts\tests\test_sov_land.py"),
                         "scripts/tests/test_sov_land.py")

    def test_a_dot_dot_segment_does_not_survive_into_the_comparison(self):
        """A relative path is not automatically inside the repository.

        `scripts/../STATUS.yaml` begins with an admitted prefix and names an
        excluded file. Resolving it first is the whole reason the exclusion list
        means anything.
        """
        self.assertEqual(tree.repo_relative("scripts/../STATUS.yaml"), "STATUS.yaml")
        self.assertEqual(tree.repo_relative("scripts/../decisions/0001-x.md"),
                         "decisions/0001-x.md")

    def test_a_relative_path_can_leave_the_repository_and_is_not_pulled_back_in(self):
        converted = tree.repo_relative("scripts/../../elsewhere/x.py")
        self.assertTrue(Path(converted).is_absolute())
        self.assertNotIn("..", converted)

    def test_an_absolute_path_that_escapes_is_reported_resolved(self):
        """A refusal that misnames the file is a refusal a reader cannot check."""
        escaping = str(ROOT / "scripts" / ".." / ".." / "elsewhere" / "x.py")
        converted = tree.repo_relative(escaping)
        self.assertNotIn("..", converted)
        self.assertTrue(Path(converted).is_absolute())

    def test_a_trailing_separator_survives_canonicalisation(self):
        """Canonicalising must never turn a refusal into a pass.

        `Path` drops a trailing separator, so `contracts/` became `contracts`.
        The boundary refuses the first and admitted the second, while `git add`
        stages the grant registry with either. `git status --porcelain` reports
        an untracked directory with exactly that trailing slash, so this arrived
        without an adversary.
        """
        self.assertEqual(tree.repo_relative("contracts/"), "contracts/")
        self.assertEqual(tree.repo_relative(r"contracts\\"), "contracts/")
        self.assertEqual(tree.repo_relative("contracts"), "contracts")

    def test_a_path_outside_the_repository_is_not_rewritten_into_scope(self):
        """The defeating case: conversion must not become a way into the grant.

        A path the repository does not contain has no repository-relative form.
        Returning it unchanged is what keeps it failing the scope check; silently
        stripping it to a tail like `scripts/x.py` would admit a file the grant
        never covered.
        """
        outside = Path(ROOT.anchor) / "elsewhere" / "scripts" / "x.py"
        converted = tree.repo_relative(str(outside))
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
            "paths": [tree.repo_relative(raw_path)],
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


class GradedSetIsWhatReachesTheTarget(unittest.TestCase):
    """The gate grades the commits it is about to move, not the tree it sits in.

    `--path` says what a landing stages. It never said what the merge carries:
    `git merge --no-ff` moves every commit already on the branch. A participant
    could commit an excluded path, land one in-scope file, and the merge took
    both, because the excluded path was never shown to the evaluator at all.
    Demonstrated on 2026-08-25 by a second session, reproduced here, and named by
    `decisions/0064` as the observation that would defeat its own ruling.
    """

    def _repo(self, tmp: str) -> Path:
        """A throwaway repository with one commit on main and one on a branch."""
        root = Path(tmp) / "repo"
        root.mkdir()
        run = lambda *a: subprocess.run(["git", *a], cwd=root, capture_output=True, check=True)
        run("init", "-q", "-b", "main")
        run("config", "user.email", "t@t")
        run("config", "user.name", "t")
        (root / "kept.py").write_text("x" + chr(10), encoding="utf-8")
        run("add", "-A")
        run("commit", "-q", "-m", "base")
        run("checkout", "-q", "-b", "work")
        (root / "excluded.yaml").write_text("y" + chr(10), encoding="utf-8")
        run("add", "-A")
        run("commit", "-q", "-m", "an excluded path, committed and never declared")
        return root

    def test_a_committed_path_is_graded_even_though_no_one_declared_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            with mock.patch.object(tree, "ROOT", root):
                carried = tree.carried_paths("main", "work")
        self.assertIn("excluded.yaml", carried)

    def test_a_branch_level_with_its_target_carries_nothing(self):
        """The control: grading the range must not invent paths on a clean branch."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            subprocess.run(["git", "checkout", "-q", "main"], cwd=root, check=True)
            subprocess.run(["git", "merge", "-q", "work"], cwd=root, check=True)
            with mock.patch.object(tree, "ROOT", root):
                carried = tree.carried_paths("main", "work")
        self.assertEqual(carried, [])

    def test_the_graded_set_is_the_union_of_staged_and_carried(self):
        """The fix itself: neither set alone is what reaches the target."""
        args = mock.Mock(path=["scripts/a.py"], target="main", observation=None,
                         actor="sov", spend=0, skip_checks=True)
        patches = (
            mock.patch.object(tree, "current_branch", return_value="work"),
            mock.patch.object(tree, "carried_paths", return_value=["decisions/x.md"]),
            mock.patch.object(tree, "_commit_span", return_value=(1, 0)),
            mock.patch.object(sov_land.sov_grant, "load_grants", return_value=[]),
        )
        for patch in patches:
            patch.start()
        try:
            request, _result, _b, _a, _be, staged, carried = sov_land._evaluate(args)
        finally:
            for patch in patches:
                patch.stop()
        self.assertEqual(request["paths"], ["decisions/x.md", "scripts/a.py"])
        self.assertEqual(staged, ["scripts/a.py"])
        self.assertEqual(carried, ["decisions/x.md"])


class ADirectoryIsAnOpenSet(unittest.TestCase):
    """A path that names a directory authorises files the landing never enumerated.

    `git add -- contracts/sub` stages everything beneath it, including files
    another session holds. A witness found that the evaluator cannot see it — it
    holds no filesystem — and that `_held_elsewhere` matched by exact string, so
    a contested file inside a permitted directory was invisible to the collision
    check and would have been committed under this landing's evidence.
    """

    def test_a_directory_is_named_so_the_caller_can_refuse_it(self):
        self.assertEqual(tree.directory_paths(["scripts"]), ["scripts"])
        self.assertEqual(tree.directory_paths(["scripts/sov_land.py"]), [])

    def test_a_contested_file_inside_a_named_directory_is_seen(self):
        """The defeating case: equality matching hid exactly this."""
        contested = [{"path": "contracts/sub/deep.json", "holder": "session-other"}]
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=json.dumps(contested), stderr="")
            held = tree._held_elsewhere(["contracts/sub"])
        self.assertEqual(len(held), 1)
        self.assertIn("contracts/sub/deep.json", held[0])

    def test_a_session_holding_the_directory_this_landing_stages_into_is_seen(self):
        """The reverse direction, which asking one way still hid.

        Another session holds `contracts/sub`; this landing stages a file under
        it. Same collision, spelled from the other side.
        """
        contested = [{"path": "contracts/sub", "holder": "session-other"}]
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=json.dumps(contested), stderr="")
            held = tree._held_elsewhere(["contracts/sub/deep.json"])
        self.assertEqual(len(held), 1)

    def test_an_unrelated_sibling_is_not_swept_in(self):
        """Containment must not become a prefix match on the string."""
        contested = [{"path": "contracts/subtle.json", "holder": "session-other"}]
        with mock.patch("subprocess.run") as run:
            run.return_value = mock.Mock(returncode=0, stdout=json.dumps(contested), stderr="")
            held = tree._held_elsewhere(["contracts/sub"])
        self.assertEqual(held, [])


class AnUnreadableRangeRefusesRatherThanCrashes(unittest.TestCase):
    """A missing target branch turned a refusal into a traceback."""

    def test_a_range_that_cannot_be_computed_is_a_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "empty"
            root.mkdir()
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=root, check=True)
            with mock.patch.object(tree, "ROOT", root):
                with self.assertRaises(tree.LandingRefused):
                    tree.carried_paths("no-such-branch", "main")


class TheEffectPathActuallyRuns(unittest.TestCase):
    """`land` is the one function here with an effect, and nothing exercised it.

    A 189-line refactor left `_git` behind in the module it moved to, so
    `cmd_land` raised `NameError` at its first git call — after the gate had
    said PERMITTED. Lint, 19 tests, the corpus and all 39 checks stayed green
    over a landing path that could not run. These cases drive the real thing in
    a throwaway repository so the next refactor cannot do that quietly.
    """

    def _repo(self, tmp: str) -> Path:
        root = Path(tmp) / "repo"
        root.mkdir()

        def run(*a):
            subprocess.run(["git", *a], cwd=root, capture_output=True, check=True)

        run("init", "-q", "-b", "main")
        run("config", "user.email", "t@t")
        run("config", "user.name", "t")
        (root / "kept.py").write_text("x" + chr(10), encoding="utf-8")
        run("add", "-A")
        run("commit", "-q", "-m", "base")
        run("checkout", "-q", "-b", "work")
        return root

    def _args(self, **over):
        base = dict(path=["kept.py"], target="main", observation=None, actor="sov",
                    spend=0, skip_checks=True, message="land: a test")
        base.update(over)
        return mock.Mock(**base)

    def test_land_reaches_git_and_commits_and_merges(self):
        """The positive case: a permitted landing actually moves the target."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            (root / "kept.py").write_text("changed" + chr(10), encoding="utf-8")
            permitted = {"verdict": authority.PERMITTED, "code": None,
                         "detail": "covered", "grant_id": "grant:test", "considered": []}
            with mock.patch.object(tree, "ROOT", root), \
                    mock.patch.object(authority, "evaluate", return_value=permitted), \
                    mock.patch.object(tree, "_held_elsewhere", return_value=[]), \
                    mock.patch.object(sov_land.sov_grant, "load_grants", return_value=[]):
                code = sov_land.cmd_land(self._args())
            merged = subprocess.run(["git", "log", "--oneline", "main"], cwd=root,
                                    capture_output=True, text=True).stdout
        self.assertEqual(code, 0)
        self.assertIn("land: a test", merged)

    def test_a_refused_landing_leaves_the_target_untouched(self):
        """The defeating case: nothing moves when the gate says no."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._repo(tmp)
            (root / "kept.py").write_text("changed" + chr(10), encoding="utf-8")
            refused = {"verdict": authority.REFUSED, "code": authority.AUTHORITY_REFUSED,
                       "detail": "no", "grant_id": None, "considered": []}
            before = subprocess.run(["git", "rev-parse", "main"], cwd=root,
                                    capture_output=True, text=True).stdout
            with mock.patch.object(tree, "ROOT", root), \
                    mock.patch.object(authority, "evaluate", return_value=refused), \
                    mock.patch.object(sov_land.sov_grant, "load_grants", return_value=[]):
                code = sov_land.cmd_land(self._args())
            after = subprocess.run(["git", "rev-parse", "main"], cwd=root,
                                   capture_output=True, text=True).stdout
        self.assertEqual(code, 1)
        self.assertEqual(before, after)


class LandRefusesABlanketStage(unittest.TestCase):
    """Sessions here share one working directory; the gate never stages what it was not given."""

    def test_land_without_explicit_paths_is_refused(self):
        self.assertEqual(sov_land.main(["land"]), 2)


if __name__ == "__main__":
    unittest.main()
