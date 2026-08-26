"""Cases for live-session coordination across worktrees.

Every case here builds its own store in a temporary directory and injects its
own timestamps, so the suite proves the logic with no session registered, no
worktree checked out, and no clock dependence - the conditions CI runs under.

Each behaviour has a positive form and a form proving the refusal or the
expiry: a guard that only ever allows is not a guard, and a claim that never
expires is a lock that wedges the repository when a session dies.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovsession import claims, commands, store  # noqa: E402

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

    def end(self, name: str, at: int = 0) -> None:
        """Close a session."""
        store.append(self.directory, store.SESSIONS_LOG, {
            "event": "end", "session": name, "at": stamp(at)})


class SessionLiveness(StoreCase):
    """A session is live until it says otherwise, or falls silent and dies."""

    def test_registered_session_reads_live(self) -> None:
        self.register("alpha")
        projected = store.sessions(self.directory, T0 + timedelta(seconds=60))
        self.assertTrue(projected["alpha"]["live"])

    def test_ended_session_reads_dead(self) -> None:
        self.register("alpha")
        self.end("alpha", at=30)
        projected = store.sessions(self.directory, T0 + timedelta(seconds=60))
        self.assertFalse(projected["alpha"]["live"])

    def test_silent_session_expires_without_releasing(self) -> None:
        """A session killed mid-write must not hold its claim forever."""
        self.register("alpha")
        late = T0 + timedelta(seconds=store.STALE_SECONDS + 1)
        self.assertFalse(store.sessions(self.directory, late)["alpha"]["live"])

    def test_heartbeat_keeps_a_session_live(self) -> None:
        self.register("alpha")
        store.append(self.directory, store.SESSIONS_LOG, {
            "event": "heartbeat", "session": "alpha",
            "at": stamp(int(store.STALE_SECONDS) - 10)})
        late = T0 + timedelta(seconds=store.STALE_SECONDS + 1)
        self.assertTrue(store.sessions(self.directory, late)["alpha"]["live"])

    def test_an_unregistered_writer_is_not_a_session(self) -> None:
        """A claim or heartbeat alone must not conjure a session with no tree."""
        store.append(self.directory, store.SESSIONS_LOG,
                     {"event": "heartbeat", "session": "ghost", "at": stamp()})
        claims.claim(self.directory, "ghost", ["scripts/verify.py"], TREE_A, at=stamp())
        at = T0 + timedelta(seconds=60)
        self.assertFalse(store.sessions(self.directory, at)["ghost"]["live"])
        self.assertEqual(claims.held(self.directory, at), {})

    def test_a_torn_line_is_skipped_not_fatal(self) -> None:
        self.register("alpha")
        with (self.directory / store.SESSIONS_LOG).open("a", encoding="utf-8") as handle:
            handle.write('{"event": "regi\n')
        self.assertIn("alpha", store.sessions(self.directory, T0))


class ProcessLiveness(unittest.TestCase):
    """Asking whether a process lives must not disturb it.

    `os.kill(pid, 0)` is the POSIX idiom and is wrong here: CPython's Windows
    implementation opens the process with PROCESS_ALL_ACCESS and calls
    TerminateProcess with the signal number as the exit code, so the question
    kills its subject. It only failed safe in this repository because opening
    the parent process was denied, which also made every live session read dead.
    """

    def test_this_process_reads_alive(self) -> None:
        self.assertTrue(store.pid_alive(os.getpid()))

    def test_an_absent_process_reads_dead(self) -> None:
        self.assertFalse(store.pid_alive(999999))

    def test_nothing_and_nonsense_read_dead(self) -> None:
        for value in (None, 0, "", "not-a-pid"):
            with self.subTest(value=value):
                self.assertFalse(store.pid_alive(value))

    def test_asking_does_not_kill_the_process_asked_about(self) -> None:
        child = subprocess.Popen(
            [sys.executable, "-c", "import sys; sys.stdin.read()"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL)
        try:
            self.assertTrue(store.pid_alive(child.pid))
            self.assertIsNone(child.poll(), "the liveness check terminated the process")
            self.assertTrue(store.pid_alive(child.pid), "still alive after asking twice")
        finally:
            child.kill()
            child.wait(timeout=10)
            if child.stdin:
                child.stdin.close()

    def test_a_finished_process_reads_dead(self) -> None:
        child = subprocess.Popen([sys.executable, "-c", "pass"])
        child.wait(timeout=10)
        self.assertFalse(store.pid_alive(child.pid))


class ClaimProjection(StoreCase):
    """Claims are held by live sessions and released by dead ones."""

    def test_a_live_session_holds_its_claim(self) -> None:
        self.register("alpha")
        claims.claim(self.directory, "alpha", ["scripts/verify.py"], TREE_A, at=stamp())
        held = claims.held(self.directory, T0 + timedelta(seconds=60))
        self.assertEqual([h["session"] for h in held["scripts/verify.py"]], ["alpha"])

    def test_release_drops_the_claim(self) -> None:
        self.register("alpha")
        claims.claim(self.directory, "alpha", ["scripts/verify.py"], TREE_A, at=stamp())
        claims.release(self.directory, "alpha", ["scripts/verify.py"], at=stamp(10))
        self.assertEqual(claims.held(self.directory, T0 + timedelta(seconds=60)), {})

    def test_a_dead_session_holds_nothing(self) -> None:
        self.register("alpha")
        claims.claim(self.directory, "alpha", ["scripts/verify.py"], TREE_A, at=stamp())
        self.end("alpha", at=10)
        self.assertEqual(claims.held(self.directory, T0 + timedelta(seconds=60)), {})

    def test_relative_normalises_an_absolute_path(self) -> None:
        root = Path(self._temp.name)
        (root / "scripts").mkdir()
        target = root / "scripts" / "verify.py"
        target.write_text("", encoding="utf-8")
        self.assertEqual(claims.relative(target, root), "scripts/verify.py")


class OutsideTheRepository(unittest.TestCase):
    """A file the repository will never see cannot collide through it.

    Sessions write scratchpad files constantly. Claiming those crowds the list
    with paths no other session could act on even if it wanted to.
    """

    def test_a_repository_path_is_inside(self) -> None:
        self.assertTrue(claims.within_repo("scripts/verify.py"))

    def test_an_absolute_path_is_outside(self) -> None:
        self.assertFalse(claims.within_repo("C:/Users/x/AppData/Local/Temp/note.md"))
        self.assertFalse(claims.within_repo("/tmp/note.md"))

    def test_a_resource_is_always_inside(self) -> None:
        """A port is not a path and must survive the check."""
        self.assertTrue(claims.within_repo("resource:port:8787"))
        self.assertTrue(claims.within_repo("resource:sqlite:.local/x.db"))


class DecisionNumbers(StoreCase):
    """A number on disk and a number a peer reserved are equally taken."""

    def setUp(self) -> None:
        super().setUp()
        self.root = Path(self._temp.name) / "repo"
        (self.root / "decisions").mkdir(parents=True)

    def _write(self, name: str) -> None:
        (self.root / "decisions" / name).write_text("", encoding="utf-8")

    def _next(self, at=T0) -> int:
        """The next number, with history search off: the fixture is not a repository."""
        return claims.next_decision_number(self.root, self.directory, at,
                                           search_history=False)

    def test_the_next_number_follows_what_is_on_disk(self) -> None:
        self._write("0001-a.md")
        self._write("0002-b.md")
        self.assertEqual(self._next(), 3)

    def test_a_peer_reservation_is_skipped(self) -> None:
        """The 0039 / 0040 / 0041 collision: three sessions, one visible maximum."""
        self._write("0038-a.md")
        self.register("alpha")
        claims.claim(self.directory, "alpha", ["decisions/0039-peer.md"], TREE_A,
                     at=stamp())
        self.assertEqual(self._next(T0 + timedelta(seconds=60)), 40)

    def test_a_dead_peers_reservation_is_released(self) -> None:
        self._write("0038-a.md")
        self.register("alpha")
        claims.claim(self.directory, "alpha", ["decisions/0039-peer.md"], TREE_A,
                     at=stamp())
        self.end("alpha", at=10)
        self.assertEqual(self._next(T0 + timedelta(seconds=60)), 39)

    def test_a_gap_is_never_reused(self) -> None:
        """A missing number means a retired record or one on an unseen branch."""
        self._write("0001-a.md")
        self._write("0003-c.md")
        self.assertEqual(self._next(), 4)

    def test_an_empty_decisions_directory_starts_at_one(self) -> None:
        self.assertEqual(self._next(), 1)

    def test_history_sees_a_number_absent_from_this_tree(self) -> None:
        """The real repository: every number ever added on any ref is spent."""
        root = Path(__file__).resolve().parents[2]
        from_history = claims.numbers_in_history(root)
        self.assertTrue(from_history, "git log --all found no decision records")
        on_disk = {int(name.name[:4]) for name in (root / "decisions").iterdir()
                   if name.name[:4].isdigit()}
        self.assertTrue(from_history >= on_disk or bool(from_history & on_disk))


class SessionIdentity(unittest.TestCase):
    """One process gets one registry name, and a launcher's name outranks a guess.

    A hook knows the session id and nothing about why the session was started.
    A launcher chose the name before the process existed and put that same name
    on the worktree, the branch lane and the Claude display. When the hook's
    derived name won, four of nine live sessions on this machine held two
    registry rows apiece and nothing could join a lane to the process running
    it.
    """

    def setUp(self) -> None:
        self._saved = {key: os.environ.get(key)
                       for key in ("SOV_SESSION", "CLAUDE_CODE_SESSION_ID")}
        for key in self._saved:
            os.environ.pop(key, None)
        self.addCleanup(self._restore)

    def _restore(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_a_typed_name_wins_over_everything(self) -> None:
        os.environ["SOV_SESSION"] = "fleet-alpha"
        self.assertEqual(commands.session_name("typed", fallback="session-abc123"),
                         "typed")

    def test_the_launcher_name_beats_a_derived_one(self) -> None:
        os.environ["SOV_SESSION"] = "fleet-alpha"
        self.assertEqual(commands.session_name(fallback="session-abc123"),
                         "fleet-alpha")

    def test_a_derived_name_is_used_when_no_launcher_named_it(self) -> None:
        os.environ["CLAUDE_CODE_SESSION_ID"] = "zzzzzzzz"
        self.assertEqual(commands.session_name(fallback="session-abc123"),
                         "session-abc123")

    def test_an_inherited_id_names_a_session_nobody_named(self) -> None:
        os.environ["CLAUDE_CODE_SESSION_ID"] = "abcdef123456"
        self.assertEqual(commands.session_name(), "session-abcdef")

    def test_an_unnamed_session_falls_back_to_its_pid(self) -> None:
        self.assertEqual(commands.session_name(), "unnamed-" + str(os.getpid()))


class HookIdentity(unittest.TestCase):
    """The shipped SessionStart hook, run as the host runs it."""

    HOOK = Path(__file__).resolve().parents[2] / ".claude" / "hooks" / "session_registry.py"

    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.tree = Path(self._temp.name) / "tree"
        self.tree.mkdir()
        for args in (["init", "-b", "main"],
                     ["config", "user.email", "t@example.invalid"],
                     ["config", "user.name", "Test"]):
            subprocess.run(["git", *args], cwd=self.tree, check=True,
                           capture_output=True)
        (self.tree / "README.md").write_text("x" + chr(10), encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=self.tree, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=self.tree, check=True,
                       capture_output=True)

    def _start(self, launcher_name: str | None) -> list[str]:
        """Fire the hook's start mode and return the names it registered."""
        env = dict(os.environ)
        env.pop("SOV_SESSION", None)
        if launcher_name:
            env["SOV_SESSION"] = launcher_name
        env["CLAUDE_CODE_SESSION_ID"] = "eeeeeeee-1111-2222-3333-444444444444"
        payload = json.dumps({"cwd": str(self.tree),
                              "session_id": "abc123def456789"})
        subprocess.run([sys.executable, str(self.HOOK), "start"],
                       input=payload, text=True, cwd=self.tree, env=env,
                       capture_output=True, check=False)
        directory = store.store_dir(self.tree)
        return [str(record.get("session")) for record in
                store.read(directory, store.SESSIONS_LOG)
                if record.get("event") == "register"]

    def test_the_hook_registers_the_name_the_launcher_chose(self) -> None:
        self.assertEqual(self._start("fleet-alpha"), ["fleet-alpha"])

    def test_the_hook_never_registers_a_second_alias(self) -> None:
        """The defeat: one process, one row. A `session-` twin is the old defect."""
        names = self._start("fleet-alpha")
        self.assertNotIn("session-abc123", names)
        self.assertEqual(len(names), 1)

    def test_an_unlaunched_session_still_gets_its_derived_name(self) -> None:
        self.assertEqual(self._start(None), ["session-abc123"])


if __name__ == "__main__":
    unittest.main()
