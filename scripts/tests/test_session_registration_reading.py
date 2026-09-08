"""Positive and defeating cases for the registration line in the session briefing.

The briefing used to render `intent: (not registered)` for two different states:
a session absent from the registry, and a registered session that named no
intent. A reader cannot act on a line that means either. These cases hold the
two apart, and the defeating case is the one that matters - a session with no
register event must not be able to read the briefing and think it holds claims.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsession import brief, store  # noqa: E402

WARNING = "NOT REGISTERED"
REMEDY = "sov_session.py register"


class RegistrationLine(unittest.TestCase):
    """`brief._registration` over the three states the store can project."""

    @staticmethod
    def lines(**data: object) -> list[str]:
        rendered: list[str] = []
        brief._registration(rendered, dict(data))
        return rendered

    def test_unregistered_session_is_warned_and_told_the_remedy(self) -> None:
        lines = self.lines(registered=False, intent="")
        joined = "\n".join(lines)
        self.assertIn(WARNING, joined)
        self.assertIn(REMEDY, joined)

    def test_registered_session_without_intent_is_not_warned(self) -> None:
        """The defeating case for the old string: this state is not unregistered."""
        joined = "\n".join(self.lines(registered=True, intent=""))
        self.assertNotIn(WARNING, joined)
        self.assertIn("(none recorded)", joined)

    def test_registered_session_reports_its_intent(self) -> None:
        joined = "\n".join(self.lines(registered=True, intent="close the audit"))
        self.assertNotIn(WARNING, joined)
        self.assertIn("close the audit", joined)

    def test_missing_key_is_treated_as_unregistered(self) -> None:
        """A caller that supplies no reading must not be told it is registered."""
        self.assertIn(WARNING, "\n".join(self.lines(intent="")))


class CollectSurfacesRegistration(unittest.TestCase):
    """`brief.collect` must carry the store's own `registered` flag through."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.directory = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_store_marks_a_registered_session(self) -> None:
        store.append(self.directory, store.SESSIONS_LOG,
                     {"event": "register", "session": "s-1", "intent": "build"})
        self.assertTrue(store.sessions(self.directory)["s-1"].get("registered"))

    def test_a_session_that_only_beat_never_registered(self) -> None:
        """A heartbeat alone conjures no registration, so the briefing must warn."""
        store.append(self.directory, store.SESSIONS_LOG,
                     {"event": "heartbeat", "session": "s-2"})
        record = store.sessions(self.directory)["s-2"]
        self.assertFalse(record.get("registered"))
        self.assertIn(WARNING, "\n".join(
            self.lines_for(bool(record.get("registered")))))

    @staticmethod
    def lines_for(registered: bool) -> list[str]:
        rendered: list[str] = []
        brief._registration(rendered, {"registered": registered, "intent": ""})
        return rendered


if __name__ == "__main__":
    unittest.main()
