"""The continuity hook must never misreport what the journal holds.

`.claude/hooks/console_session.py` is host plumbing: it holds no standing and
writes no console state (`AGENTS.md`, Local orchestration harness). What it does
hold is the first thing a starting session reads, so a wrong sentence there is a
false claim about the record that every later turn inherits.

The load-bearing cases drive `main`, because `main` is the function that printed
the false sentence and `main` is what the hook event actually calls. A case that
can only fail because a private helper does not exist yet proves the helper was
added, not that the behaviour changed; those are kept, but they are not what the
repair rests on.
"""

from __future__ import annotations

from pathlib import Path
import contextlib
import importlib.util
import io
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "console_session.py"

TRACEBACK = '''Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "core.py", line 192, in reconstruct
    raise BrokenChain(entry["entry_id"])
soveraeign_record_service.core.BrokenChain: entry_80767935e18c488fb45502df9d5c385e'''

FAULT = ("soveraeign_record_service.core.BrokenChain: "
         "entry_80767935e18c488fb45502df9d5c385e")

# The sentence this repair exists to delete. The pre-repair hook printed it after
# committing an open-session event and its receipt.
FALSE_CLAIM = "Nothing was recorded"


def _hook():
    """Load the hook by path; `.claude/hooks` is not an importable package."""
    spec = importlib.util.spec_from_file_location("console_session_hook", HOOK)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HookHarness(unittest.TestCase):
    """Drive the hook the way the SessionStart event does, over stubbed calls."""

    def setUp(self) -> None:
        self.hook = _hook()
        self.calls: list[str] = []
        self.remembered: list[tuple[str, str]] = []
        self.bindings: dict[str, str] = {}
        self.hook._bindings = lambda: dict(self.bindings)
        self.hook._remember = self._remember
        # Grant bootstrapping is a different concern and shells out on its own.
        # These cases are about what the hook says when a briefing fails, so the
        # bootstrap is stubbed rather than asserted on. Left live, every expected
        # call list here would also have to name whatever `NEEDED` currently holds,
        # and would break again the next time a capability is added to it.
        self.hook._ensure_grants = lambda: None
        # `run_main` feeds the hook its event on stdin, and the hook module shares
        # one `subprocess` with every other test in this process. Both are put back
        # afterwards; leaving either replaced fails modules that shell out.
        self.addCleanup(setattr, sys, "stdin", sys.stdin)
        self.addCleanup(setattr, subprocess, "run", subprocess.run)

    def patch_run(self, fake) -> None:
        """Replace `subprocess.run` for one case only."""
        subprocess.run = fake

    def _remember(self, host: str, console: str) -> None:
        self.remembered.append((host, console))

    def _console_opens_then_fails(self, *args: str) -> dict[str, str]:
        """open-session commits a record; the briefing that follows cannot be read."""
        self.calls.append(args[0])
        if args[0] == "open-session":
            return {"session_id": "session_opened"}
        raise RuntimeError(TRACEBACK)

    def run_main(self, action: str = "start", event: str = '{"session_id": "host-1"}') -> str:
        sys.stdin = io.StringIO(event)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = self.hook.main(["console_session.py", action])
        self.assertEqual(code, 0, "the hook must never break a session")
        return buffer.getvalue()


class TheFalseClaim(HookHarness):
    """The defect itself, driven through the function that carried it."""

    def test_a_failed_briefing_after_a_committed_open_does_not_claim_an_empty_record(
            self) -> None:
        """The pre-repair hook printed FALSE_CLAIM here, over a record it just wrote."""
        self.hook._console = self._console_opens_then_fails
        output = self.run_main()
        self.assertEqual(self.calls, ["open-session", "session-context"],
                         "the open is asked for before the briefing, and commits")
        self.assertNotIn(FALSE_CLAIM, output)
        self.assertIn("session_opened", output)

    def test_the_briefing_failure_is_reported_as_a_failed_read(self) -> None:
        self.hook._console = self._console_opens_then_fails
        output = self.run_main()
        self.assertIn("briefing", output.lower())
        self.assertIn(FAULT, output)
        self.assertIn("Nothing here says the journal lost anything", output)

    def test_a_traceback_does_not_reach_the_starting_session(self) -> None:
        self.hook._console = self._console_opens_then_fails
        output = self.run_main()
        self.assertNotIn("Traceback", output)
        self.assertNotIn("<frozen runpy>", output)

    def test_the_hook_exits_zero_even_when_everything_fails(self) -> None:
        def refuse_everything(*_: str) -> dict[str, str]:
            raise RuntimeError(TRACEBACK)

        self.hook._console = refuse_everything
        output = self.run_main()
        self.assertNotIn(FALSE_CLAIM, output)


class WhatResumedMayAssert(HookHarness):
    """A session id from the binding map is not evidence the session exists.

    `_bindings` documents itself as a host convenience and not a record. `end`
    never removes an entry, so the map keeps naming sessions that are CLOSED with
    their cursor already pinned, and it survives a store replaced underneath it.
    Reporting such an id as "resumed" asserts the console still holds an open
    session, which this hook has not checked. That is the same unbacked claim the
    repair exists to stop making.
    """

    def setUp(self) -> None:
        super().setUp()
        self.bindings = {"host-1": "session_from_the_map"}
        self.hook._console = self._console_opens_then_fails

    def test_a_mapped_id_is_not_reported_as_a_resumed_session(self) -> None:
        output = self.run_main()
        self.assertIn("session_from_the_map", output)
        self.assertNotIn("resumed from an earlier session", output)

    def test_a_mapped_id_says_the_map_is_not_a_record(self) -> None:
        output = self.run_main()
        self.assertIn("not a record", output)
        self.assertIn("unchecked here", output)

    def test_nothing_is_opened_when_the_map_already_names_one(self) -> None:
        self.run_main()
        self.assertEqual(self.calls, ["session-context"])
        self.assertEqual(self.remembered, [])

    def test_an_opened_id_may_say_a_record_committed(self) -> None:
        """The other half: what the hook opened itself, it may assert."""
        self.bindings = {}
        output = self.run_main()
        self.assertIn("the console committed that record", output)


class ARefusalIsNotASuccess(HookHarness):
    """The CLI answers a refusal on stdout and exits non-zero.

    Reading stdout alone cannot tell a refusal from a result, so a refused call
    used to return the refusal dict and fail at whichever key the caller looked up
    next. The session was told the cause was a missing dict key and never saw the
    reason code.
    """

    def _run(self, code: int, stdout: str, stderr: str = ""):
        self.patch_run(
            lambda *_a, **_kw: subprocess.CompletedProcess([], code, stdout, stderr))
        return self.hook._console("open-session")

    def test_a_refusal_raises_and_carries_its_reason_code(self) -> None:
        with self.assertRaises(self.hook.ConsoleRefused) as refused:
            self._run(2, '{"outcome": "REFUSED", "reason_code": "NO_LIVE_GRANT"}')
        self.assertEqual(refused.exception.reason_code, "NO_LIVE_GRANT")
        self.assertEqual(refused.exception.command, "open-session")

    def test_the_reason_code_reaches_the_session(self) -> None:
        self.patch_run(lambda *_a, **_kw: subprocess.CompletedProcess(
            [], 2, '{"outcome": "REFUSED", "reason_code": "NO_LIVE_GRANT"}', ""))
        output = self.run_main()
        self.assertIn("NO_LIVE_GRANT", output)
        self.assertNotIn("'session_id'", output, "a KeyError is not the cause")

    def test_a_zero_exit_is_still_read_as_a_result(self) -> None:
        self.assertEqual(self._run(0, '{"session_id": "session_ok"}'),
                         {"session_id": "session_ok"})

    def test_a_non_json_failure_keeps_a_stable_reason_code(self) -> None:
        with self.assertRaises(self.hook.ConsoleRefused) as refused:
            self._run(1, "", "the store is locked")
        self.assertEqual(refused.exception.reason_code, "REFUSED")
        self.assertIn("the store is locked", str(refused.exception))


class AKnownRecordIsNotHedged(HookHarness):
    """A binding that will not write does not make the committed open unknown."""

    def setUp(self) -> None:
        super().setUp()

        def refuse_to_remember(*_: str) -> None:
            raise OSError("host-sessions.json is read-only")

        self.hook._remember = refuse_to_remember
        self.hook._console = self._console_opens_then_fails

    def test_the_open_is_reported_as_committed(self) -> None:
        output = self.run_main()
        self.assertIn("session_opened", output)
        self.assertIn("the console committed that record", output)
        self.assertNotIn("unknown from here", output)

    def test_the_cost_of_the_lost_binding_is_named(self) -> None:
        output = self.run_main()
        self.assertIn("will open a second one", output)
        self.assertIn("host-sessions.json is read-only", output)


class TerseFailure(unittest.TestCase):
    """A failure reaches session context as the line naming the fault."""

    def setUp(self) -> None:
        self.hook = _hook()

    def test_keeps_only_the_naming_line(self) -> None:
        self.assertEqual(self.hook._terse(RuntimeError(TRACEBACK)), FAULT)

    def test_a_trailing_warning_is_not_reported_as_the_cause(self) -> None:
        """A warning emitted on exit lands after the fault and would win a naive scan."""
        noisy = TRACEBACK + "\nsys:1: ResourceWarning: unclosed database"
        self.assertEqual(self.hook._terse(RuntimeError(noisy)), FAULT)

    def test_falls_back_to_the_type_when_there_is_no_message(self) -> None:
        self.assertEqual(self.hook._terse(ValueError("   ")), "ValueError")

    def test_a_failure_that_is_only_warnings_still_reports_something(self) -> None:
        only = "sys:1: ResourceWarning: unclosed database"
        self.assertEqual(self.hook._terse(RuntimeError(only)), only)


if __name__ == "__main__":
    unittest.main()


class AGrantRefusalIsNotAHookFailure(HookHarness):
    """`_ensure_grants` sits before start()'s try, so a refusal there escaped it.

    Found by soveraeign-53 witnessing this branch: the case is a store whose permits
    office was opened by another operator, where `grant` genuinely refuses. Every
    other case in this file stubs `_ensure_grants` to nothing, which is right for
    them and is exactly why this path went untested.

    Grants are a precondition for recording, not for reading. A refusal must cost
    the session its grants and nothing else - not its briefing, and above all not
    the honest report, which is the whole point of this branch.
    """

    def setUp(self) -> None:
        super().setUp()

        def refuse_the_grant() -> None:
            raise self.hook.ConsoleRefused(
                "grant", '{"reason_code": "NO_LIVE_GRANT", "outcome": "REFUSED"}', 2, "")

        self.hook._ensure_grants = refuse_the_grant

    def test_the_session_is_still_briefed(self) -> None:
        """The failure this repairs: main()'s catch-all replaced the whole report."""
        self.hook._console = lambda *args: {"session_id": "session_opened"} \
            if args[0] == "open-session" else {"entries": [], "unread": 0}
        out = self.run_main()
        self.assertNotIn("Console continuity unavailable", out)
        self.assertIn("grants were not established", out)

    def test_the_reason_code_reaches_the_session(self) -> None:
        self.hook._console = lambda *args: {"session_id": "session_opened"} \
            if args[0] == "open-session" else {"entries": [], "unread": 0}
        self.assertIn("NO_LIVE_GRANT", self.run_main())

    def test_the_note_says_what_it_costs(self) -> None:
        self.hook._console = lambda *args: {"session_id": "session_opened"} \
            if args[0] == "open-session" else {"entries": [], "unread": 0}
        out = self.run_main()
        self.assertIn("briefed without them", out)
        self.assertIn("may refuse for the same reason", out)

    def test_a_refused_grant_and_a_failed_briefing_both_report(self) -> None:
        """Two independent failures. Neither may hide the other."""
        self.hook._console = self._console_opens_then_fails
        out = self.run_main()
        self.assertIn("briefing could not be built", out)
        self.assertIn("NO_LIVE_GRANT", out)
        self.assertIn("Nothing here says the journal lost anything", out)

    def test_the_hook_still_exits_zero(self) -> None:
        self.hook._console = self._console_opens_then_fails
        self.run_main()  # run_main asserts the exit code
