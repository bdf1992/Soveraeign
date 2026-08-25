"""Cases for branch, worktree, and merge management.

Every case builds a throwaway git repository in a temporary directory and asserts against
that, so the suite proves the logic with no network, no branch of this repository, and no
dependence on what happens to be checked out while it runs.

Each behaviour has a positive form and a form proving the refusal or the failure. The
refusals matter more than the successes here: a merge planner that only ever reports
success would send a run into a conflict it had already been told about, and a retirement
command that deletes whatever it is handed will eventually be handed the trunk.
"""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovbranch import execute, gitio, ledger, mergeplan, render  # noqa: E402

NL = chr(10)

IDENTITY = ["-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
            "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main"]


def git(root: Path, *args: str) -> str:
    """Run one git command in the fixture repository and return its stdout."""
    done = subprocess.run(["git", *IDENTITY, *args], cwd=str(root),
                          capture_output=True, text=True, check=False)
    if done.returncode != 0 and args[0] not in ("merge", "branch"):
        raise AssertionError(f"git {' '.join(args)} failed: {done.stderr or done.stdout}")
    return done.stdout.strip()


def write(root: Path, name: str, text: str) -> None:
    """Put a file in the fixture tree with the line endings the repository pins."""
    (root / name).write_text(text, encoding="utf-8", newline="\n")


def commit(root: Path, message: str) -> str:
    """Stage everything in the fixture tree and commit it."""
    git(root, "add", "-A")
    git(root, "commit", "-m", message)
    return git(root, "rev-parse", "HEAD")


TEMPLATE: dict[str, object] = {}
"""One built fixture repository, copied per case.

Building it costs a dozen git invocations, and on this host a git invocation is the
expensive part of the suite. Thirty cases each building their own put the run past the
graded budget in `scripts/verify.py` on its own, so it is built once and copied.
"""


def setUpModule() -> None:
    """Build the one fixture repository every case works from a copy of."""
    holder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
    root = Path(holder.name) / "template"
    root.mkdir()
    git(root, "init")
    git(root, "config", "user.name", "Fixture")
    git(root, "config", "user.email", "fixture@example.invalid")
    write(root, "a.txt", "one" + NL)
    write(root, "b.txt", "one" + NL)
    base = commit(root, "root")
    git(root, "branch", "feature", base)
    git(root, "branch", "quiet", base)
    write(root, "a.txt", "trunk" + NL)
    commit(root, "trunk changes a.txt")
    git(root, "checkout", "feature")
    write(root, "a.txt", "feature" + NL)
    commit(root, "feature changes a.txt")
    git(root, "checkout", "quiet")
    write(root, "b.txt", "quiet" + NL)
    commit(root, "quiet changes b.txt")
    git(root, "checkout", "main")
    TEMPLATE.update(holder=holder, root=root)


def tearDownModule() -> None:
    """Drop the fixture repository."""
    holder = TEMPLATE.get("holder")
    if holder is not None:
        holder.cleanup()


def _copy(holder: tempfile.TemporaryDirectory) -> Path:
    """A private copy of the fixture repository inside a temporary directory."""
    root = Path(holder.name) / "repo"
    shutil.copytree(TEMPLATE["root"], root)
    return root


class ReadOnlyRepoCase(unittest.TestCase):
    """One copy of the fixture shared by every case in the class.

    For cases that move no ref and write no file, a copy per case buys nothing and costs
    the largest share of this suite's wall time, which `scripts/verify.py` grades.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._holder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.root = _copy(cls._holder)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._holder.cleanup()


class RepoCase(unittest.TestCase):
    """A copy of the fixture per case: a trunk, a branch that merges, and one that conflicts."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = _copy(self._temp)

    def tearDown(self) -> None:
        self._temp.cleanup()

    def resolve_merge(self, branch: str, into: str, name: str, text: str) -> str:
        """Merge `into` on top of `branch`, settle the conflict, and return the new tip."""
        git(self.root, "checkout", branch)
        git(self.root, "merge", into)
        write(self.root, name, text)
        git(self.root, "add", "-A")
        git(self.root, "commit", "--no-edit", "-m", f"merge {into} into {branch}")
        tip = git(self.root, "rev-parse", "HEAD")
        git(self.root, "checkout", "main")
        return tip


class ProbeCase(ReadOnlyRepoCase):
    """The object-database merge probe, which must never touch a working tree."""

    def test_clean_merge_reports_a_tree(self) -> None:
        clean, tree, conflicts = gitio.probe(self.root, "main", "quiet")
        self.assertTrue(clean)
        self.assertIsNotNone(tree)
        self.assertEqual(conflicts, [])

    def test_conflict_names_the_file_and_writes_no_tree(self) -> None:
        clean, tree, conflicts = gitio.probe(self.root, "main", "feature")
        self.assertFalse(clean)
        self.assertIsNone(tree)
        self.assertEqual(conflicts, ["a.txt"])

    def test_probe_leaves_the_working_tree_untouched(self) -> None:
        before = git(self.root, "status", "--porcelain"), git(self.root, "rev-parse", "HEAD")
        gitio.probe(self.root, "main", "feature")
        gitio.probe(self.root, "main", "quiet")
        after = git(self.root, "status", "--porcelain"), git(self.root, "rev-parse", "HEAD")
        self.assertEqual(before, after)

    def test_missing_ref_is_refused_rather_than_guessed(self) -> None:
        clean, tree, conflicts = gitio.probe(self.root, "main", "no-such-branch")
        self.assertFalse(clean)
        self.assertIsNone(tree)
        self.assertEqual(len(conflicts), 1)
        self.assertIn("no-such-branch", conflicts[0])
        self.assertIn("could not merge", conflicts[0])

    def test_chain_records_the_merge_without_moving_any_ref(self) -> None:
        heads_before = git(self.root, "for-each-ref", "--format=%(refname) %(objectname)")
        _, tree, _ = gitio.probe(self.root, "main", "quiet")
        chained = gitio.chain(self.root, tree, "main", "quiet")
        self.assertIsNotNone(chained)
        self.assertEqual(git(self.root, "rev-parse", f"{chained}^{{tree}}"), tree)
        self.assertEqual(heads_before,
                         git(self.root, "for-each-ref", "--format=%(refname) %(objectname)"))


class PlanCase(ReadOnlyRepoCase):
    """The rolling simulation, and the retry that makes it worth running."""

    def entries(self, *names: str) -> list[dict]:
        """Minimal ledger entries for the named local branches, in the order given."""
        return [{"name": name, "local": True, "remote": None, "ahead": 1, "when": index}
                for index, name in enumerate(names)]

    def test_a_clean_branch_lands_and_a_conflicting_one_is_blocked(self) -> None:
        record = mergeplan.build(self.root, "main", self.entries("quiet", "feature"),
                                 how="given", retry=False)
        self.assertEqual([step["name"] for step in record["steps"]], ["quiet"])
        self.assertEqual([step["name"] for step in record["blocked"]], ["feature"])
        self.assertEqual(record["blocked"][0]["conflicts"], ["a.txt"])

    def test_the_accumulation_carries_forward(self) -> None:
        record = mergeplan.build(self.root, "main", self.entries("quiet"), how="given")
        self.assertNotEqual(record["steps"][0]["result"], record["base_commit"][:12])

    def test_ordering_by_size_puts_the_smallest_first(self) -> None:
        entries = [{"name": "big", "ahead": 9, "when": 1}, {"name": "small", "ahead": 1,
                                                            "when": 2}]
        ordered = mergeplan.order_refs(entries, "smallest")
        self.assertEqual([entry["name"] for entry in ordered], ["small", "big"])

    def test_a_base_that_does_not_exist_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            mergeplan.build(self.root, "no-such-base", self.entries("quiet"))


class PlanRetryCase(RepoCase):
    """The second pass, which is the only reason a conflict is deferred rather than dropped."""

    def entries(self, *names: str) -> list[dict]:
        """Minimal ledger entries for the named local branches, in the order given."""
        return [{"name": name, "local": True, "remote": None, "ahead": 1, "when": index}
                for index, name in enumerate(names)]

    def test_a_branch_that_has_absorbed_the_base_merges_back_cleanly(self) -> None:
        self.resolve_merge("feature", "main", "a.txt", "settled" + NL)
        record = mergeplan.build(self.root, "main", self.entries("feature"),
                                 how="given", retry=False)
        self.assertEqual(record["blocked"], [])
        self.assertEqual([step["name"] for step in record["steps"]], ["feature"])

    def test_retry_is_what_separates_the_two_passes(self) -> None:
        settled = self.resolve_merge("feature", "main", "a.txt", "settled" + NL)
        git(self.root, "branch", "settled", settled)
        git(self.root, "branch", "-f", "feature", "feature~1")
        candidates = self.entries("feature", "settled")
        without = mergeplan.build(self.root, "main", candidates, how="given", retry=False)
        self.assertEqual([step["name"] for step in without["blocked"]], ["feature"])
        with_retry = mergeplan.build(self.root, "main", candidates, how="given", retry=True)
        self.assertEqual(with_retry["blocked"], [])
        self.assertEqual([step["name"] for step in with_retry["steps"]], ["settled", "feature"])


class LedgerCase(unittest.TestCase):
    """The disposition rules, which decide what is safe to delete."""

    def entry(self, **overrides) -> dict:
        """A blank ledger record with the fields a case cares about set."""
        record = ledger._blank(overrides.pop("name", "feat/x"))
        record.update(local=True)
        record.update(overrides)
        return record

    def test_a_contained_branch_is_merged_and_retirable(self) -> None:
        record = self.entry(ahead=0)
        ledger._judge(record)
        self.assertEqual(record["disposition"], ledger.MERGED)
        self.assertTrue(record["retirable"])

    def test_a_live_session_outranks_containment(self) -> None:
        record = self.entry(ahead=0, session="session-abc")
        ledger._judge(record)
        self.assertEqual(record["disposition"], ledger.HELD)
        self.assertFalse(record["retirable"])

    def test_a_protected_branch_is_never_retirable(self) -> None:
        record = self.entry(name="main", ahead=0, protected=True)
        ledger._judge(record)
        self.assertEqual(record["disposition"], ledger.MERGED)
        self.assertFalse(record["retirable"])

    def test_commits_only_on_origin_hold_the_branch_back(self) -> None:
        record = self.entry(ahead=0, remote_ahead=3)
        ledger._judge(record)
        self.assertFalse(record["retirable"])

    def test_a_dirty_worktree_holds_the_branch_back(self) -> None:
        record = self.entry(ahead=0, dirty=True)
        ledger._judge(record)
        self.assertFalse(record["retirable"])

    def test_a_deleted_upstream_with_work_left_is_orphaned(self) -> None:
        record = self.entry(ahead=2, gone=True)
        ledger._judge(record)
        self.assertEqual(record["disposition"], ledger.ORPHANED)

    def test_a_probed_conflict_outranks_a_probed_success(self) -> None:
        conflicted, ready = self.entry(ahead=1, clean=False), self.entry(ahead=1, clean=True)
        ledger._judge(conflicted)
        ledger._judge(ready)
        self.assertEqual(conflicted["disposition"], ledger.CONFLICTED)
        self.assertEqual(ready["disposition"], ledger.READY)
        self.assertLess(ledger.ORDER.index(ledger.CONFLICTED), ledger.ORDER.index(ledger.READY))


class LedgerReadCase(ReadOnlyRepoCase):
    """The ledger read against a real repository, including the trunk protection."""

    def test_the_base_branch_is_protected_and_not_retirable(self) -> None:
        entries = {entry["name"]: entry for entry in ledger.build(self.root, "main")}
        self.assertTrue(entries["main"]["protected"])
        self.assertFalse(entries["main"]["retirable"])

    def test_every_local_branch_is_positioned_against_the_base(self) -> None:
        entries = {entry["name"]: entry for entry in ledger.build(self.root, "main")}
        self.assertEqual(set(entries), {"main", "feature", "quiet"})
        self.assertEqual(entries["quiet"]["ahead"], 1)
        self.assertEqual(entries["feature"]["behind"], 1)

    def test_probing_records_the_conflict_on_the_branch_that_has_one(self) -> None:
        entries = {entry["name"]: entry for entry in ledger.build(self.root, "main", probe=True)}
        self.assertEqual(entries["feature"]["disposition"], ledger.CONFLICTED)
        self.assertEqual(entries["feature"]["conflicts"], ["a.txt"])
        self.assertEqual(entries["quiet"]["disposition"], ledger.READY)


def plan_for(*names: str) -> list[dict]:
    """Steps in the shape `integrate` consumes."""
    return [{"name": name, "ref": name, "clean": True, "ahead": 1} for name in names]


class IntegrateCase(unittest.TestCase):
    """One landing run, asserted from three directions.

    The run is performed once for the class rather than once per case. Creating a worktree
    is the most expensive thing this suite does, and all three cases are statements about
    the same single run.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls._holder = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.root = _copy(cls._holder)
        cls.target = Path(cls._holder.name) / "integration"
        cls.before = (git(cls.root, "rev-parse", "HEAD"),
                      git(cls.root, "status", "--porcelain"))
        cls.record = execute.integrate(cls.root, "main", plan_for("quiet"),
                                       "integration/test", cls.target, verify=False)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._holder.cleanup()

    def test_a_clean_sequence_lands_in_a_new_worktree(self) -> None:
        self.assertEqual([step["name"] for step in self.record["merged"]], ["quiet"])
        self.assertIsNone(self.record["failed"])
        self.assertEqual((self.target / "b.txt").read_text(encoding="utf-8"), "quiet" + NL)

    def test_the_original_tree_is_left_where_it_was(self) -> None:
        after = git(self.root, "rev-parse", "HEAD"), git(self.root, "status", "--porcelain")
        self.assertEqual(self.before, after)

    def test_nothing_is_pushed_and_the_command_is_only_printed(self) -> None:
        self.assertIn("push -u origin integration/test", self.record["push"])
        self.assertIn("nothing was pushed", render.integrate(self.record))
        self.assertEqual(git(self.root, "remote"), "")


class IntegrateRefusalCase(RepoCase):
    """What landing refuses to do, which is the half that protects an occupied tree."""

    def target(self) -> Path:
        """A path for the integration worktree that does not exist yet."""
        return Path(self._temp.name) / "integration"

    def test_a_conflict_stops_the_run_and_leaves_the_tree_to_inspect(self) -> None:
        record = execute.integrate(self.root, "main", plan_for("quiet", "feature"),
                                   "integration/test", self.target(), verify=False)
        self.assertEqual([step["name"] for step in record["merged"]], ["quiet"])
        self.assertEqual(record["failed"]["name"], "feature")
        self.assertEqual(record["failed"]["reason"], "conflict")
        self.assertTrue(self.target().is_dir())
        self.assertEqual(git(self.target(), "status", "--porcelain"), "")

    def test_an_existing_branch_name_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            execute.integrate(self.root, "main", plan_for("quiet"), "feature",
                              self.target(), verify=False)

    def test_an_existing_path_is_refused(self) -> None:
        self.target().mkdir()
        with self.assertRaises(ValueError):
            execute.integrate(self.root, "main", plan_for("quiet"), "integration/test",
                              self.target(), verify=False)


class NoGitIdentityCase(RepoCase):
    """A host with no configured git identity, which is what CI is.

    Git refuses to write a commit without one, and it refuses in a way that reads exactly
    like a failed merge. Before this was separated, the planner reported every branch as
    unmergeable and the merger reported a conflict, on a repository where everything
    merged cleanly.
    """

    def setUp(self) -> None:
        super().setUp()
        git(self.root, "config", "--unset-all", "user.name")
        git(self.root, "config", "--unset-all", "user.email")
        self._environment = dict(os.environ)
        os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)
        for name in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL",
                     "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL"):
            os.environ.pop(name, None)

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._environment)
        super().tearDown()

    def test_git_reports_no_committer(self) -> None:
        self.assertIsNone(gitio.committer(self.root))

    def test_planning_still_works_because_probe_commits_carry_their_own_author(self) -> None:
        entries = [{"name": "quiet", "local": True, "ahead": 1, "when": 0}]
        record = mergeplan.build(self.root, "main", entries, how="given")
        self.assertEqual([step["name"] for step in record["steps"]], ["quiet"])
        self.assertEqual(record["blocked"], [])

    def test_merging_refuses_up_front_instead_of_reporting_a_conflict(self) -> None:
        target = Path(self._temp.name) / "integration"
        with self.assertRaises(RuntimeError) as raised:
            execute.integrate(self.root, "main", plan_for("quiet"), "integration/test",
                              target, verify=False)
        self.assertIn("identity", str(raised.exception))
        self.assertFalse(target.exists())


class RetireCase(RepoCase):
    """Deleting what the base already holds, and refusing everything else."""

    def ledger_for(self, name: str, **overrides) -> list[dict]:
        """One retirable-looking record for `name`, with overrides applied last."""
        record = ledger._blank(name)
        record.update(local=True, ahead=0, retirable=True)
        record.update(overrides)
        return [record]

    def test_a_dry_run_deletes_nothing(self) -> None:
        git(self.root, "branch", "spent", "main")
        actions = execute.retire(self.root, self.ledger_for("spent"), dry_run=True)
        self.assertEqual([action["name"] for action in actions], ["spent"])
        self.assertFalse(actions[0]["deleted"])
        self.assertIn("spent", git(self.root, "branch", "--list", "spent"))

    def test_applying_deletes_the_contained_branch(self) -> None:
        git(self.root, "branch", "spent", "main")
        actions = execute.retire(self.root, self.ledger_for("spent"), dry_run=False)
        self.assertTrue(actions[0]["deleted"])
        self.assertEqual(git(self.root, "branch", "--list", "spent"), "")

    def test_a_branch_not_marked_retirable_is_skipped_entirely(self) -> None:
        actions = execute.retire(self.root, self.ledger_for("feature", retirable=False),
                                 dry_run=False)
        self.assertEqual(actions, [])
        self.assertIn("feature", git(self.root, "branch", "--list", "feature"))

    def test_the_report_says_so_when_nothing_is_safe_to_retire(self) -> None:
        self.assertIn("nothing is safe to retire", render.retire([], dry_run=True))


if __name__ == "__main__":
    unittest.main()
