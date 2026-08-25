"""Defeating cases for the composed surface's SOV session harness bridge."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovsurface import session_presence  # noqa: E402


class SessionPresence(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        script = self.root / "scripts" / "sov_session.py"
        script.parent.mkdir(parents=True)
        script.write_text("# test session cli\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    @staticmethod
    def result(payload: object, code: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["python"], returncode=code,
            stdout=json.dumps(payload) if not isinstance(payload, str) else payload,
            stderr=stderr,
        )

    def test_snapshot_reads_only_live_sessions_from_sov_cli(self) -> None:
        payload = {
            "sessions": [
                {"session": "session-live", "live": True, "branch": "feat/live"},
                {"session": "session-ended", "live": False, "branch": "feat/old"},
            ],
            "held": {},
        }
        seen: list[list[str]] = []

        def runner(args, **kwargs):
            seen.append(args)
            return self.result(payload)

        data = session_presence.snapshot(self.root, runner=runner)
        self.assertTrue(data["available"])
        self.assertEqual([item["session"] for item in data["sessions"]], ["session-live"])
        self.assertEqual(seen[0][-2:], ["list", "--json"])

    def test_missing_session_runtime_stays_an_explicit_harness_omission(self) -> None:
        (self.root / "scripts" / "sov_session.py").unlink()
        data = session_presence.snapshot(self.root)
        self.assertFalse(data["available"])
        self.assertIn("not present", data["reason"])
        self.assertEqual(data["sessions"], [])

    def test_renderer_never_registers_implicitly(self) -> None:
        calls: list[list[str]] = []

        def runner(args, **kwargs):
            calls.append(args)
            return self.result({"sessions": [], "held": {}})

        session_presence.snapshot(self.root, runner=runner)
        self.assertEqual(len(calls), 1)
        self.assertNotIn("register", calls[0])

    def test_explicit_registration_crosses_only_the_sov_session_cli(self) -> None:
        calls: list[list[str]] = []

        def runner(args, **kwargs):
            calls.append(args)
            return self.result({"session": "session-abc"})

        ok, detail = session_presence.register(
            self.root, name="session-abc", intent="surface integration", runner=runner,
        )
        self.assertTrue(ok, detail)
        command = calls[0]
        self.assertIn("register", command)
        self.assertIn("--name", command)
        self.assertIn("session-abc", command)
        self.assertIn("--intent", command)
        self.assertIn("surface integration", command)

    def test_session_cards_are_harness_not_node_presence(self) -> None:
        data = {
            "available": True,
            "source": "scripts/sov_session.py list --json",
            "reason": "",
            "sessions": [{
                "session": "session-2628a1",
                "live": True,
                "branch": "feat/session-principal",
                "intent": "name the principal",
                "principal": "principal:claude-code",
                "verification": "UNVERIFIED",
            }],
            "held": {"scripts/x.py": [{"session": "session-2628a1"}]},
        }
        fragment = session_presence.fragment(data)
        self.assertIn("HARNESS", fragment)
        self.assertIn("session-2628a1", fragment)
        self.assertIn("principal:claude-code", fragment)
        self.assertIn("UNVERIFIED", fragment)
        self.assertIn("Presence grants no authority", fragment)
        self.assertNotIn("ACTION", fragment)

    def test_decorating_presence_does_not_rewrite_node_interface_digest(self) -> None:
        page = (
            '<aside class="utility"><h3>No live presence implied</h3>'
            '<p>This shell does not fake an Active Now list.</p>'
            '</aside><footer class="status">NODE INTERFACE · abc123 · not an observation</footer>'
        )
        data = {
            "available": True,
            "source": "scripts/sov_session.py list --json",
            "reason": "",
            "sessions": [{"session": "session-a", "live": True}],
            "held": {},
        }
        decorated = session_presence.decorate(page, data)
        self.assertIn("session-a", decorated)
        self.assertIn("Harness presence is explicit", decorated)
        self.assertIn("NODE INTERFACE · abc123 · not an observation", decorated)
        self.assertIn("host harness state, not governed Node state", decorated)


if __name__ == "__main__":
    unittest.main()
