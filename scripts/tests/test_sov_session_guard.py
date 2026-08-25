"""Cases for the guards that stand between a session and someone else's work.

The store and the claim projection are proved in `test_sov_session.py`; this
module proves only the judgements built on top of them - what is refused, what
is merely reported, and what is left alone.

Every guard has a case proving it refuses and a case proving it does not. A
guard that only ever allows is decoration, and one that only ever refuses is a
wedge: on 2026-08-24 a hook that failed closed on a wiring error stopped every
session in this repository at once.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovsession import claims, guard, store  # noqa: E402

T0 = datetime(2026, 8, 23, 20, 0, 0, tzinfo=timezone.utc)
TREE_A = "C:/repo"
TREE_B = "C:/repo-worktree"


def stamp(offset_seconds: int = 0) -> str:
    """A fixed timestamp offset from T0, in the form the store writes."""
    moment = T0 + timedelta(seconds=offset_seconds)
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")



class StoreCase(unittest.TestCase):
    """A temporary store, and a helper for registering fictional sessions."""

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.directory = Path(self._temp.name) / "sov-sessions"
        self.addCleanup(self._temp.cleanup)

    def register(self, name: str, tree: str = TREE_A, branch: str = "feat/x",
                 at: int = 0) -> None:
        """Register a session with no live process behind it."""
        store.append(self.directory, store.SESSIONS_LOG, {
            "event": "register", "session": name, "pid": 0,
            "tree": tree, "branch": branch, "at": stamp(at),
        })


class WriteGuard(StoreCase):
    """The lost-update case is refused; the merge-conflict case is only reported."""

    def _hold(self, session: str, tree: str, path: str = "scripts/verify.py") -> None:
        self.register(session, tree=tree)
        claims.claim(self.directory, session, [path], tree, at=stamp())

    def test_unheld_path_is_allowed(self) -> None:
        verdict = guard.guard_write(self.directory, "beta", "scripts/verify.py", TREE_A,
                                    T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.ALLOW)

    def test_same_tree_holder_denies_the_write(self) -> None:
        self._hold("alpha", TREE_A)
        verdict = guard.guard_write(self.directory, "beta", "scripts/verify.py", TREE_A,
                                    T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.DENY)
        self.assertIn("alpha", verdict["reason"])
        self.assertTrue(verdict["escape"], "a deny must name a way through")

    def test_cross_tree_holder_only_warns(self) -> None:
        self._hold("alpha", TREE_B)
        verdict = guard.guard_write(self.directory, "beta", "scripts/verify.py", TREE_A,
                                    T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.WARN)
        self.assertEqual(verdict["conflicts"][0]["kind"], claims.CROSS_TREE)

    def test_a_session_is_not_blocked_by_its_own_claim(self) -> None:
        self._hold("alpha", TREE_A)
        verdict = guard.guard_write(self.directory, "alpha", "scripts/verify.py", TREE_A,
                                    T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.ALLOW)

    def test_a_cold_claim_degrades_to_a_report(self) -> None:
        """A file edited hours ago and moved on from is not a lock on the repository."""
        self._hold("alpha", TREE_A)
        cold = T0 + timedelta(seconds=guard.HOT_SECONDS + 60)
        verdict = guard.guard_write(self.directory, "beta", "scripts/verify.py",
                                    TREE_A, cold)
        self.assertEqual(verdict["decision"], guard.WARN)
        self.assertIn("same working tree", verdict["reason"])

    def test_a_hot_claim_still_denies(self) -> None:
        self._hold("alpha", TREE_A)
        hot = T0 + timedelta(seconds=guard.HOT_SECONDS - 60)
        verdict = guard.guard_write(self.directory, "beta", "scripts/verify.py",
                                    TREE_A, hot)
        self.assertEqual(verdict["decision"], guard.DENY)

    def test_an_expired_claim_stops_denying(self) -> None:
        self._hold("alpha", TREE_A)
        late = T0 + timedelta(seconds=store.STALE_SECONDS + 1)
        verdict = guard.guard_write(self.directory, "beta", "scripts/verify.py",
                                    TREE_A, late)
        self.assertEqual(verdict["decision"], guard.ALLOW)


class BashGuard(StoreCase):
    """Blanket staging is refused only where it can sweep someone else's work."""

    def test_blanket_add_is_allowed_when_alone_in_the_tree(self) -> None:
        verdict = guard.guard_bash(self.directory, "alpha", "git add -A", TREE_A,
                                   T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.ALLOW)

    def test_blanket_add_is_denied_in_a_shared_tree(self) -> None:
        self.register("beta", tree=TREE_A)
        verdict = guard.guard_bash(self.directory, "alpha", "git add -A", TREE_A,
                                   T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.DENY)
        self.assertIn("beta", verdict["reason"])

    def test_a_peer_in_another_tree_does_not_block_a_blanket_add(self) -> None:
        self.register("beta", tree=TREE_B)
        verdict = guard.guard_bash(self.directory, "alpha", "git add -A", TREE_A,
                                   T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.ALLOW)

    def test_every_blanket_shape_is_caught(self) -> None:
        self.register("beta", tree=TREE_A)
        for command in ("git add -A", "git add --all", "git add .",
                        "git commit -a -m x", "git commit -am x", "git commit --all"):
            with self.subTest(command=command):
                verdict = guard.guard_bash(self.directory, "alpha", command, TREE_A,
                                           T0 + timedelta(seconds=60))
                self.assertEqual(verdict["decision"], guard.DENY, command)

    def test_an_explicit_pathspec_is_not_a_blanket_add(self) -> None:
        self.register("beta", tree=TREE_A)
        for command in ("git add scripts/verify.py", "git commit -m 'x'",
                        "git add scripts/ docs/"):
            with self.subTest(command=command):
                verdict = guard.guard_bash(self.directory, "alpha", command, TREE_A,
                                           T0 + timedelta(seconds=60))
                self.assertEqual(verdict["decision"], guard.ALLOW, command)

    def test_destructive_commands_are_denied_in_a_shared_tree(self) -> None:
        self.register("beta", tree=TREE_A)
        for command in ("git reset --hard", "git clean -fd", "git checkout -- ."):
            with self.subTest(command=command):
                verdict = guard.guard_bash(self.directory, "alpha", command, TREE_A,
                                           T0 + timedelta(seconds=60))
                self.assertEqual(verdict["decision"], guard.DENY, command)

    def test_a_gate_piped_into_tail_is_reported_even_when_alone(self) -> None:
        """The pipeline's exit status is tail's, so the `&&` fires over a red run."""
        command = "python scripts/verify.py 2>&1 | tail -2 && git commit -m x"
        verdict = guard.guard_bash(self.directory, "alpha", command, TREE_A,
                                   T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.WARN)
        self.assertIn("exit status", verdict["reason"])

    def test_a_gate_read_directly_is_not_reported(self) -> None:
        command = "python scripts/verify.py --json > out.json && git commit -m x"
        verdict = guard.guard_bash(self.directory, "alpha", command, TREE_A,
                                   T0 + timedelta(seconds=60))
        self.assertEqual(verdict["decision"], guard.ALLOW)


STAGE_ALL = "git" + " add -A"
"""Assembled rather than written, so this file does not read as the command itself."""


class CommandData(unittest.TestCase):
    """Text a command carries is not a command the shell runs.

    A bare substring match refused the edit that introduced this class: the
    docstring explaining the guard contained the staging command it guards
    against. Anchoring on a command boundary and blanking quoted and heredoc
    spans is what separates an invocation from a sentence about one.
    """

    def _blanket(self, command: str) -> bool:
        return bool(guard.BLANKET_ADD.search(guard.scrub(command)))

    def test_a_bare_invocation_is_caught(self) -> None:
        self.assertTrue(self._blanket(STAGE_ALL))

    def test_an_invocation_after_a_separator_is_caught(self) -> None:
        for prefix in ("cd /x && ", "cd /x; ", "true | "):
            with self.subTest(prefix=prefix):
                self.assertTrue(self._blanket(prefix + STAGE_ALL))

    def test_the_same_text_inside_double_quotes_is_not(self) -> None:
        self.assertFalse(self._blanket('echo "never run ' + STAGE_ALL + ' here"'))

    def test_the_same_text_inside_single_quotes_is_not(self) -> None:
        self.assertFalse(self._blanket("echo 'do not " + STAGE_ALL + "'"))

    def test_the_same_text_inside_a_heredoc_is_not(self) -> None:
        body = "python - <<PY\nprint('do not use " + STAGE_ALL + "')\nPY"
        self.assertFalse(self._blanket(body))

    def test_a_word_ending_in_git_is_not_an_invocation(self) -> None:
        self.assertFalse(self._blanket("mygit add -A"))

    def test_an_explicit_pathspec_survives_scrubbing(self) -> None:
        self.assertFalse(self._blanket("git add scripts/verify.py"))


class CommandTarget(unittest.TestCase):
    """Where a command will actually run, which is not where the session stands.

    A session standing in the shared tree writes `cd ../sov-budget && git add -A`
    routinely. Judging that against the shared tree refused a blanket stage in a
    worktree its author had entirely to itself - the one place the isolation was
    real, and the one place the guard should say nothing.
    """

    def test_a_bare_command_names_no_directory(self) -> None:
        for command in ("git add -A", "git commit -a", "echo cd nothing here"):
            with self.subTest(command=command):
                self.assertEqual(guard.target_directory(command), "")

    def test_a_leading_cd_retargets_the_command(self) -> None:
        self.assertEqual(guard.target_directory("cd ../sov-budget && git add -A"),
                         "../sov-budget")

    def test_a_cd_after_a_semicolon_counts(self) -> None:
        self.assertEqual(guard.target_directory("cd /c/x; git add ."), "/c/x")

    def test_git_dash_c_retargets_one_command(self) -> None:
        self.assertEqual(guard.target_directory("git -C C:/repo/wt add -A"),
                         "C:/repo/wt")

    def test_a_quoted_directory_keeps_its_spaces(self) -> None:
        self.assertEqual(guard.target_directory('cd "../sov budget" && git add -A'),
                         "../sov budget")

    def test_the_last_directory_named_wins(self) -> None:
        self.assertEqual(guard.target_directory("cd /a && cd /b && git add -A"), "/b")


class TreePeers(StoreCase):
    """Who else is standing in this exact checkout."""

    def test_only_the_same_tree_counts(self) -> None:
        self.register("beta", tree=TREE_A)
        self.register("gamma", tree=TREE_B)
        peers = guard.tree_peers(self.directory, "alpha", TREE_A,
                                 T0 + timedelta(seconds=60))
        self.assertEqual([peer["session"] for peer in peers], ["beta"])

    def test_a_session_is_not_its_own_peer(self) -> None:
        self.register("alpha", tree=TREE_A)
        peers = guard.tree_peers(self.directory, "alpha", TREE_A,
                                 T0 + timedelta(seconds=60))
        self.assertEqual(peers, [])


if __name__ == "__main__":
    unittest.main()
