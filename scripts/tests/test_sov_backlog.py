"""Tests for the unlanded-work survey and the distinctions a disposition rests on.

Three readings decide what happens to a branch, and each has a way of being wrong that
looks like an answer. A branch whose work already landed by another route reads as
abandoned unless patches are compared rather than hashes. A branch that conflicts reads
as mergeable unless the merge is actually attempted. A file two branches both change
reads as safe until the second one lands. Each is proved here against real throwaway
repositories, because the warrant of the survey is that it measures git rather than
reporting what a branch says about itself.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_backlog  # noqa: E402


def git(cwd: Path, *args: str) -> str:
    """Run one git command in a scratch repository and fail loudly if it does not work."""
    done = subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)
    return done.stdout.strip()


def write(work: Path, name: str, body: str) -> None:
    """Write one file with the line endings the repository pins."""
    (work / name).write_text(body, encoding="utf-8", newline="\n")


def seed(work: Path) -> None:
    """Create a repository with one commit on `main`."""
    work.mkdir(parents=True, exist_ok=True)
    git(work, "init", "--initial-branch=main")
    git(work, "config", "user.email", "test@example.invalid")
    git(work, "config", "user.name", "Test")
    write(work, "shared.txt", "base\n")
    git(work, "add", "shared.txt")
    git(work, "commit", "-m", "base")


def diverge(work: Path) -> None:
    """Move `main` forward so a later cherry-pick cannot fast-forward onto it.

    Without this the pick produces the identical commit rather than an equivalent one,
    and a test meant to prove patch comparison proves only hash comparison. The first
    version of these tests had exactly that hole and passed while empty.
    """
    git(work, "checkout", "main")
    write(work, "trunk-moved.txt", "moved\n")
    git(work, "add", "trunk-moved.txt")
    git(work, "commit", "-m", "trunk moves on")


class BacklogSurveyTest(unittest.TestCase):
    """Measure a branch by what git says about it, never by what it claims."""

    def survey_in(self, build) -> dict:
        with tempfile.TemporaryDirectory() as raw:
            work = Path(raw) / "work"
            seed(work)
            build(work)
            git(work, "checkout", "main")
            original = sov_backlog.ROOT
            sov_backlog.ROOT = work
            try:
                return sov_backlog.survey()
            finally:
                sov_backlog.ROOT = original

    def test_a_conflicting_branch_names_the_paths(self) -> None:
        """A merge is attempted, not assumed, and the contested paths are reported."""

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/side")
            write(work, "shared.txt", "side\n")
            git(work, "commit", "-am", "side edit")
            git(work, "checkout", "main")
            write(work, "shared.txt", "trunk\n")
            git(work, "commit", "-am", "trunk edit")

        reading = self.survey_in(build)
        row = reading["branches"][0]
        self.assertEqual(row["branch"], "feat/side")
        self.assertEqual(row["conflicts"], ["shared.txt"])
        self.assertEqual(row["outstanding"], 1)

    def test_a_clean_branch_reports_no_conflict(self) -> None:
        """The defeating case: work that merges mechanically must not be flagged."""

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/side")
            write(work, "only-here.txt", "side\n")
            git(work, "add", "only-here.txt")
            git(work, "commit", "-m", "side file")

        reading = self.survey_in(build)
        row = reading["branches"][0]
        self.assertEqual(row["conflicts"], [])
        self.assertEqual(row["touches"], ["only-here.txt"])

    def test_work_already_landed_by_another_route_is_recognised(self) -> None:
        """A cherry-picked commit is present work, not abandoned work.

        Comparing hashes would call this branch outstanding and invite deleting real
        work or landing it twice. Comparing patches sees that the trunk has it.
        """

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/side")
            write(work, "feature.txt", "feature\n")
            git(work, "add", "feature.txt")
            git(work, "commit", "-m", "the feature")
            head = git(work, "rev-parse", "HEAD")
            diverge(work)
            git(work, "cherry-pick", head)

        row = self.survey_in(build)["branches"][0]
        self.assertEqual(row["outstanding"], 0)
        self.assertEqual(row["already_on_trunk"], 1)

    def test_a_partly_landed_branch_separates_what_remains(self) -> None:
        """Done and outstanding are counted apart, so neither hides the other."""

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/side")
            write(work, "first.txt", "first\n")
            git(work, "add", "first.txt")
            git(work, "commit", "-m", "first")
            landed = git(work, "rev-parse", "HEAD")
            write(work, "second.txt", "second\n")
            git(work, "add", "second.txt")
            git(work, "commit", "-m", "second")
            diverge(work)
            git(work, "cherry-pick", landed)

        row = self.survey_in(build)["branches"][0]
        self.assertEqual(row["already_on_trunk"], 1)
        self.assertEqual(row["outstanding"], 1)

    def test_a_branch_that_exists_only_on_a_remote_is_surveyed(self) -> None:
        """The defeating case this survey was blind to until 2026-08-27.

        A branch pushed and never checked out here has no `refs/heads/` entry, so a
        survey reading only local heads reports it as nothing at all. Eighteen such
        branches carrying 88 commits were invisible, one of them with an open pull
        request - in the one tool whose whole purpose is finding unlanded work.
        """

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/pushed-then-forgotten")
            write(work, "remote-only.txt", "work\n")
            git(work, "add", "remote-only.txt")
            git(work, "commit", "-m", "work nobody checked out again")
            # A bare clone standing in for the remote, then drop the local head so the
            # only thing naming this work is refs/remotes/.
            bare = work.parent / "origin.git"
            git(work, "init", "--bare", str(bare))
            git(work, "remote", "add", "origin", str(bare))
            git(work, "push", "-q", "origin", "main", "feat/pushed-then-forgotten")
            git(work, "checkout", "main")
            git(work, "branch", "-D", "feat/pushed-then-forgotten")
            git(work, "fetch", "-q", "origin")

        reading = self.survey_in(build)
        names = [row["branch"] for row in reading["branches"]]
        self.assertIn("origin/feat/pushed-then-forgotten", names)
        row = next(r for r in reading["branches"]
                   if r["branch"] == "origin/feat/pushed-then-forgotten")
        self.assertEqual(row["outstanding"], 1)
        self.assertEqual(row["touches"], ["remote-only.txt"])

    def test_a_remote_copy_of_a_local_branch_is_not_counted_twice(self) -> None:
        """The over-fire case. `origin/feat/x` and `feat/x` are one piece of work, and
        reporting both would inflate every count this survey exists to be trusted on."""

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/side")
            write(work, "only-here.txt", "side\n")
            git(work, "add", "only-here.txt")
            git(work, "commit", "-m", "side file")
            bare = work.parent / "origin2.git"
            git(work, "init", "--bare", str(bare))
            git(work, "remote", "add", "origin", str(bare))
            git(work, "push", "-q", "origin", "main", "feat/side")
            git(work, "fetch", "-q", "origin")

        reading = self.survey_in(build)
        names = [row["branch"] for row in reading["branches"]]
        self.assertEqual(names.count("feat/side"), 1)
        self.assertNotIn("origin/feat/side", names)

    def test_a_file_two_branches_change_is_named(self) -> None:
        """Contested files are surfaced before landing order turns into a conflict."""

        def build(work: Path) -> None:
            git(work, "checkout", "-b", "feat/one")
            write(work, "shared.txt", "one\n")
            git(work, "commit", "-am", "one")
            git(work, "checkout", "main")
            git(work, "checkout", "-b", "feat/two")
            write(work, "shared.txt", "two\n")
            git(work, "commit", "-am", "two")

        shared = self.survey_in(build)["shared_files"]
        self.assertIn("shared.txt", shared)
        self.assertEqual(sorted(shared["shared.txt"]), ["feat/one", "feat/two"])

    def test_a_checkout_with_no_trunk_measures_nothing_and_says_so(self) -> None:
        """Absence of a trunk is reported as unmeasurable, never as an empty backlog."""
        with tempfile.TemporaryDirectory() as raw:
            original = sov_backlog.ROOT
            sov_backlog.ROOT = Path(raw)
            try:
                reading = sov_backlog.survey()
            finally:
                sov_backlog.ROOT = original
        self.assertEqual(reading["trunk"], "")
        self.assertIn("nothing can be measured", reading["note"])


if __name__ == "__main__":
    unittest.main()
