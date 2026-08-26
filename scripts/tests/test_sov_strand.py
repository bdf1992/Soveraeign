"""Tests for the stranded-work reading and the one condition it refuses to pass.

The check exists because nobody notices work left behind, so the case that matters
most is the negative one: a branch with no upstream must fail, and a branch that has
a remote copy must not. Both are proved here against real throwaway repositories
rather than against a mocked git, because the whole warrant of the check is that it
reads git and never a participant's report about git.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_strand  # noqa: E402


def git(cwd: Path, *args: str) -> None:
    """Run one git command in a scratch repository, failing loudly if it does not work."""
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def build(root: Path, *, with_remote: bool, push_as: str = "") -> None:
    """Create a repository with `main` and one branch carrying a commit beyond it.

    `push_as` publishes the branch under a different name, which is the case that
    defeated the first version of this check: an upstream was configured, so the
    branch read as safe, while its commits had never reached any remote.
    """
    origin = root / "origin.git"
    work = root / "work"
    work.mkdir()
    git(work, "init", "--initial-branch=main")
    git(work, "config", "user.email", "test@example.invalid")
    git(work, "config", "user.name", "Test")
    (work / "seed.txt").write_text("seed\n", encoding="utf-8", newline="\n")
    git(work, "add", "seed.txt")
    git(work, "commit", "-m", "seed")
    git(work, "checkout", "-b", "feat/side")
    (work / "side.txt").write_text("side\n", encoding="utf-8", newline="\n")
    git(work, "add", "side.txt")
    git(work, "commit", "-m", "side")
    if with_remote or push_as:
        subprocess.run(["git", "init", "--bare", str(origin)], check=True, capture_output=True)
        git(work, "remote", "add", "origin", str(origin))
    if with_remote:
        git(work, "push", "-u", "origin", "feat/side")
    elif push_as:
        git(work, "push", "origin", f"feat/side:{push_as}")
        git(work, "fetch", "origin")
    git(work, "checkout", "main")


class StrandedWorkTest(unittest.TestCase):
    """Grade a branch by whether another copy of it exists, not by whether it is merged."""

    def measure(self, *, with_remote: bool,
                push_as: str = "") -> list[sov_strand.Branch]:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build(root, with_remote=with_remote, push_as=push_as)
            original = sov_strand.ROOT
            sov_strand.ROOT = root / "work"
            try:
                return sov_strand.branches(sov_strand.trunk())
            finally:
                sov_strand.ROOT = original

    def test_branch_with_no_upstream_is_at_risk(self) -> None:
        """A branch that exists in no other copy is the one condition that fails."""
        found = self.measure(with_remote=False)
        self.assertEqual([item.name for item in found], ["feat/side"])
        self.assertEqual(found[0].verdict, sov_strand.AT_RISK)
        self.assertEqual(found[0].ahead, 1)

    def test_branch_with_an_upstream_is_only_unlanded(self) -> None:
        """A pushed branch is untidy, not lost, and must never fail the check."""
        found = self.measure(with_remote=True)
        self.assertEqual([item.name for item in found], ["feat/side"])
        self.assertEqual(found[0].verdict, sov_strand.UNLANDED)

    def test_commits_pushed_under_another_name_are_not_at_risk(self) -> None:
        """Reachability from any remote ref is the question, never the upstream setting.

        This is the case that defeated the first version: two branches were reported
        at risk whose commits already sat on the remote under a different name.
        """
        found = self.measure(with_remote=False, push_as="feat/renamed-there")
        self.assertEqual(found[0].verdict, sov_strand.UNLANDED)
        self.assertEqual(found[0].unreachable, 0)

    def test_shared_history_is_counted_once(self) -> None:
        """Nested branches must not each contribute the commits they hold in common."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build(root, with_remote=False)
            work = root / "work"
            git(work, "branch", "feat/nested", "feat/side")
            original = sov_strand.ROOT
            sov_strand.ROOT = work
            try:
                against = sov_strand.trunk()
                found = sov_strand.branches(against)
                total = sov_strand.distinct(found, sov_strand.AT_RISK, against)
            finally:
                sov_strand.ROOT = original
        self.assertEqual(len(found), 2)
        self.assertEqual(sum(item.unreachable for item in found), 2)
        self.assertEqual(total, 1)

    def test_brief_is_silent_when_nothing_is_at_risk(self) -> None:
        """Session start hears nothing unless something would actually be lost."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build(root, with_remote=True)
            original = sov_strand.ROOT
            sov_strand.ROOT = root / "work"
            try:
                self.assertEqual(sov_strand.brief(), "")
            finally:
                sov_strand.ROOT = original

    def test_brief_names_the_branch_when_work_would_be_lost(self) -> None:
        """The reading names what is at risk, so nobody has to go looking for it."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build(root, with_remote=False)
            original = sov_strand.ROOT
            sov_strand.ROOT = root / "work"
            try:
                reading = sov_strand.brief()
            finally:
                sov_strand.ROOT = original
        self.assertIn("feat/side", reading)
        self.assertIn("only on this disk", reading)

    def test_a_checkout_with_no_trunk_grades_nothing_and_says_so(self) -> None:
        """Absence of a trunk is reported as ungradeable, never as a clean reading."""
        with tempfile.TemporaryDirectory() as raw:
            original = sov_strand.ROOT
            sov_strand.ROOT = Path(raw)
            try:
                self.assertEqual(sov_strand.trunk(), "")
                self.assertEqual(sov_strand.brief(), "")
            finally:
                sov_strand.ROOT = original


if __name__ == "__main__":
    unittest.main()
