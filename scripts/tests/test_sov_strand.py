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
from sovstrand import containment, reading  # noqa: E402


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
            original = reading.ROOT
            reading.ROOT = root / "work"
            try:
                return sov_strand.branches(sov_strand.trunk())
            finally:
                reading.ROOT = original

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
            original = reading.ROOT
            reading.ROOT = work
            try:
                against = sov_strand.trunk()
                found = sov_strand.branches(against)
                total = sov_strand.distinct(found, sov_strand.AT_RISK, against)
            finally:
                reading.ROOT = original
        self.assertEqual(len(found), 2)
        self.assertEqual(sum(item.unreachable for item in found), 2)
        self.assertEqual(total, 1)

    def test_brief_is_silent_when_nothing_is_at_risk(self) -> None:
        """Session start hears nothing unless something would actually be lost."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build(root, with_remote=True)
            original = reading.ROOT
            reading.ROOT = root / "work"
            try:
                self.assertEqual(sov_strand.brief(), "")
            finally:
                reading.ROOT = original

    def test_brief_names_the_branch_when_work_would_be_lost(self) -> None:
        """The reading names what is at risk, so nobody has to go looking for it."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            build(root, with_remote=False)
            original = reading.ROOT
            reading.ROOT = root / "work"
            try:
                text = sov_strand.brief()
            finally:
                reading.ROOT = original
        self.assertIn("feat/side", text)
        self.assertIn("only on this disk", text)

    def test_a_checkout_with_no_trunk_grades_nothing_and_says_so(self) -> None:
        """Absence of a trunk is reported as ungradeable, never as a clean reading."""
        with tempfile.TemporaryDirectory() as raw:
            original = reading.ROOT
            reading.ROOT = Path(raw)
            try:
                self.assertEqual(sov_strand.trunk(), "")
                self.assertEqual(sov_strand.brief(), "")
            finally:
                reading.ROOT = original


class ContainmentTest(unittest.TestCase):
    """Grade uncommitted content by whether any ref holds it, not by whether it is tidy.

    This class exists because of a real loss. On 2026-08-27 `acceptance/A11.json`, a
    finished acceptance packet, was destroyed in a working tree several sessions were
    writing at once. It had never been a commit, so no branch reading could see it, and
    the check printed PASS over that tree for as long as it was exposed.
    """

    def scratch(self, root: Path) -> Path:
        """Build a one-commit repository and return its working tree."""
        work = root / "work"
        work.mkdir()
        git(work, "init", "--initial-branch=main")
        git(work, "config", "user.email", "test@example.invalid")
        git(work, "config", "user.name", "Test")
        (work / "seed.txt").write_text("seed\n", encoding="utf-8", newline="\n")
        git(work, "add", "seed.txt")
        git(work, "commit", "-m", "seed")
        return work

    def test_a_committed_file_is_not_exposed(self) -> None:
        """Content some ref already holds is contained, whichever ref put it there."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            self.assertEqual(containment.exposed_paths(work), [])

    def test_an_untracked_file_is_exposed(self) -> None:
        """The defeating case: content that is real work and that nothing holds."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "packet.json").write_text('{"claim": "done"}\n',
                                              encoding="utf-8", newline="\n")
            self.assertEqual(containment.exposed_paths(work), ["packet.json"])

    def test_a_modified_tracked_file_is_exposed(self) -> None:
        """Being tracked is not containment: only these exact bytes count."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "seed.txt").write_text("changed\n", encoding="utf-8", newline="\n")
            self.assertEqual(containment.exposed_paths(work), ["seed.txt"])

    def test_an_ignored_file_is_not_work(self) -> None:
        """What .gitignore excludes is excluded here, or every build output would fail."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / ".gitignore").write_text("junk/\n", encoding="utf-8", newline="\n")
            (work / "junk").mkdir()
            (work / "junk" / "out.bin").write_text("x\n", encoding="utf-8", newline="\n")
            self.assertNotIn("junk/out.bin", containment.exposed_paths(work))

    def test_capture_contains_it_and_the_next_reading_agrees(self) -> None:
        """Containing exposed work is what clears it, and the check re-reads the result
        rather than taking the capture's own word for it."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "packet.json").write_text('{"claim": "done"}\n',
                                              encoding="utf-8", newline="\n")
            bare = containment.exposed_paths(work)
            commit = containment.capture(
                work, bare, "refs/rescue/test", "rescue: test capture\n")
            self.assertTrue(commit)
            matched, drifted = containment.verify(work, commit)
            self.assertEqual((matched, drifted), (1, []))
            self.assertEqual(containment.exposed_paths(work), [])

    def test_a_second_capture_never_drops_what_the_first_held(self) -> None:
        """The defect the first run of contain had: replacing a rescue ref un-rescues.

        The second capture sees only what is exposed at that moment. If it replaces the
        ref, every path the first capture held and this one did not is dropped, which is
        the loss the whole check exists to prevent.
        """
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "first.json").write_text("one\n", encoding="utf-8", newline="\n")
            containment.capture(work, ["first.json"], "refs/rescue/test", "one\n")
            (work / "second.json").write_text("two\n", encoding="utf-8", newline="\n")
            commit = containment.capture(
                work, ["second.json"], "refs/rescue/test", "two\n")
            held = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", commit],
                cwd=work, capture_output=True, text=True, check=True).stdout.split()
            self.assertEqual(sorted(held), ["first.json", "second.json"])

    def test_a_second_capture_takes_the_newer_bytes(self) -> None:
        """Where both captures carry a path, the live content is the one worth keeping."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            target = work / "packet.json"
            target.write_text("old\n", encoding="utf-8", newline="\n")
            containment.capture(work, ["packet.json"], "refs/rescue/test", "old\n")
            target.write_text("new\n", encoding="utf-8", newline="\n")
            commit = containment.capture(
                work, ["packet.json"], "refs/rescue/test", "new\n")
            matched, drifted = containment.verify(work, commit)
            self.assertEqual((matched, drifted), (1, []))


    def test_capture_never_touches_the_shared_index(self) -> None:
        """A tree with other sessions in it must survive the rescue that protects it."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "packet.json").write_text("{}\n", encoding="utf-8", newline="\n")
            before = (work / ".git" / "index").read_bytes()
            containment.capture(work, ["packet.json"], "refs/rescue/test", "rescue\n")
            self.assertEqual((work / ".git" / "index").read_bytes(), before)

    def test_verify_reports_drift_rather_than_repairing_it(self) -> None:
        """A file that changed after capture is named, not quietly re-taken."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "packet.json").write_text("first\n", encoding="utf-8", newline="\n")
            commit = containment.capture(
                work, ["packet.json"], "refs/rescue/test", "rescue\n")
            (work / "packet.json").write_text("second\n", encoding="utf-8", newline="\n")
            matched, drifted = containment.verify(work, commit)
            self.assertEqual(matched, 0)
            self.assertEqual(drifted, ["packet.json"])

    def test_the_grade_fails_on_exposed_content_with_no_stranded_commit(self) -> None:
        """The exact condition that graded PASS while a packet was one mistake from gone."""
        with tempfile.TemporaryDirectory() as raw:
            work = self.scratch(Path(raw))
            (work / "packet.json").write_text("{}\n", encoding="utf-8", newline="\n")
            original = reading.ROOT
            reading.ROOT = work
            try:
                code = sov_strand.report(
                    "main", [], [], sov_strand.uncommitted(), sov_strand.exposed())
                self.assertEqual(code, 1)
                self.assertIn("packet.json", sov_strand.brief())
                self.assertIn("held by no ref", sov_strand.brief())
            finally:
                reading.ROOT = original



if __name__ == "__main__":
    unittest.main()
