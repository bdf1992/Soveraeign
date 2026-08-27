"""The continuity hook must never misreport what the journal holds.

`.claude/hooks/console_session.py` is host plumbing: it holds no standing and
writes no console state (`AGENTS.md`, Local orchestration harness). What it does
hold is the first thing a starting session reads, so a wrong sentence there is a
false claim about the record that every later turn inherits.

The hook opens a console session before it asks for a briefing. The open commits
a record; the briefing only reads one. These cases pin that a failed briefing is
reported as a failed read and never as an empty record.
"""

from __future__ import annotations

from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "console_session.py"

TRACEBACK = '''Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "core.py", line 192, in reconstruct
    raise BrokenChain(entry["entry_id"])
soveraeign_record_service.core.BrokenChain: entry_80767935e18c488fb45502df9d5c385e'''


def _hook():
    """Load the hook by path; `.claude/hooks` is not an importable package."""
    spec = importlib.util.spec_from_file_location("console_session_hook", HOOK)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TerseFailure(unittest.TestCase):
    """A failure reaches session context as its last line, never its frames."""

    def setUp(self) -> None:
        self.hook = _hook()

    def test_keeps_only_the_naming_line(self) -> None:
        terse = self.hook._terse(RuntimeError(TRACEBACK))
        self.assertEqual(
            terse,
            "soveraeign_record_service.core.BrokenChain: "
            "entry_80767935e18c488fb45502df9d5c385e",
        )

    def test_drops_the_frames(self) -> None:
        terse = self.hook._terse(RuntimeError(TRACEBACK))
        self.assertNotIn("Traceback", terse)
        self.assertNotIn("<frozen runpy>", terse)

    def test_falls_back_to_the_type_when_there_is_no_message(self) -> None:
        self.assertEqual(self.hook._terse(ValueError("   ")), "ValueError")


class DegradedBriefing(unittest.TestCase):
    """A briefing that cannot be built says so without claiming an empty record."""

    def setUp(self) -> None:
        self.hook = _hook()
        self.failure = RuntimeError(TRACEBACK)

    def test_names_the_session_it_opened(self) -> None:
        text = self.hook._degraded("session_abc", True, self.failure)
        self.assertIn("session_abc", text)
        self.assertIn("opened and recorded", text)

    def test_names_a_resumed_session_as_resumed(self) -> None:
        text = self.hook._degraded("session_abc", False, self.failure)
        self.assertIn("resumed from an earlier session", text)
        self.assertNotIn("opened and recorded", text)

    def test_never_claims_nothing_was_recorded(self) -> None:
        """The defeating case: the sentence this repair exists to delete."""
        for opened in (True, False):
            text = self.hook._degraded("session_abc", opened, self.failure)
            self.assertNotIn("Nothing was recorded", text)

    def test_names_what_the_session_does_not_know(self) -> None:
        text = self.hook._degraded("session_abc", True, self.failure)
        self.assertIn("What this session does not know", text)
        self.assertIn("BrokenChain", text)
        self.assertNotIn("Traceback", text)


class StartDegradesRatherThanRaising(unittest.TestCase):
    """A read that fails must not take the whole hook down with it."""

    def setUp(self) -> None:
        self.hook = _hook()
        self.calls: list[str] = []

    def _console(self, *args: str) -> dict[str, str]:
        self.calls.append(args[0])
        if args[0] == "open-session":
            return {"session_id": "session_opened"}
        raise RuntimeError(TRACEBACK)

    def test_a_failed_briefing_still_reports_the_open(self) -> None:
        self.hook._console = self._console
        self.hook._bindings = lambda: {"host-1": "session_bound"}
        self.hook._remember = lambda *_: None
        text = self.hook.start({"session_id": "host-1"})
        self.assertIn("session_bound", text)
        self.assertNotIn("Nothing was recorded", text)
        self.assertEqual(self.calls, ["session-context"])

    def test_an_unbound_session_is_opened_before_the_briefing_is_asked(self) -> None:
        self.hook._console = self._console
        self.hook._bindings = lambda: {}
        self.hook._remember = lambda *_: None
        text = self.hook.start({"session_id": "host-2"})
        self.assertEqual(self.calls, ["open-session", "session-context"])
        self.assertIn("session_opened", text)
        self.assertIn("opened and recorded", text)


if __name__ == "__main__":
    unittest.main()
