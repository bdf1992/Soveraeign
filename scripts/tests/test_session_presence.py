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
    def result(
        payload: object, code: int = 0, stderr: str = "",
    ) -> subprocess.CompletedProcess[str]:
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

    def test_the_snapshot_keeps_ended_sessions_the_source_reported(self) -> None:
        payload = {
            "sessions": [
                {"session": "session-live", "live": True, "branch": "feat/live"},
                {"session": "session-ended", "live": False, "branch": "feat/old"},
            ],
            "held": {},
        }
        data = session_presence.snapshot(self.root, runner=lambda a, **k: self.result(payload))
        self.assertEqual([item["session"] for item in data["sessions"]], ["session-live"])
        self.assertEqual(
            [item["session"] for item in data["records"]],
            ["session-live", "session-ended"],
        )

    def test_a_refusing_cli_is_an_unavailable_source_not_an_empty_one(self) -> None:
        def runner(args, **kwargs):
            return self.result("", code=2, stderr="not a git repository")

        data = session_presence.snapshot(self.root, runner=runner)
        self.assertFalse(data["available"])
        self.assertIn("not a git repository", data["reason"])
        self.assertEqual(data["records"], [])

    def test_non_json_output_is_refused_rather_than_guessed(self) -> None:
        def runner(args, **kwargs):
            return self.result("three sessions are live")

        data = session_presence.snapshot(self.root, runner=runner)
        self.assertFalse(data["available"])
        self.assertIn("non-JSON", data["reason"])
        self.assertEqual(data["records"], [])

    def test_the_adapter_is_a_boundary_and_exposes_no_renderer(self) -> None:
        """Naming two absent functions proved nothing; the whole surface is pinned.

        A renderer added here under any name would put HTML behind the CLI
        boundary, where the module docstring says nothing renders.
        """
        public = {
            name for name, value in vars(session_presence).items()
            if not name.startswith("_") and callable(value)
            and getattr(value, "__module__", "") == session_presence.__name__
        }
        self.assertEqual(public, {"snapshot", "register"})
        source = Path(session_presence.__file__).read_text(encoding="utf-8")
        for markup in ("<div", "<span", "<section", "class=", "html.escape"):
            self.assertNotIn(markup, source)

    def test_the_real_subprocess_path_reads_a_cli_that_actually_runs(self) -> None:
        """Every other case injects a runner; this one crosses the real boundary."""
        script = self.root / "scripts" / "sov_session.py"
        script.write_text(
            "import json\n"
            "print(json.dumps({'sessions': [{'session': 's1', 'live': True}],"
            " 'held': {'a/path': [{'session': 's1'}]}}))\n",
            encoding="utf-8",
        )
        data = session_presence.snapshot(self.root)
        self.assertTrue(data["available"], data["reason"])
        self.assertEqual([item["session"] for item in data["sessions"]], ["s1"])
        self.assertEqual(data["held"], {"a/path": [{"session": "s1"}]})

    def test_the_real_subprocess_path_refuses_a_cli_that_exits_nonzero(self) -> None:
        script = self.root / "scripts" / "sov_session.py"
        script.write_text(
            "import sys\nprint('not a git repository', file=sys.stderr)\nsys.exit(2)\n",
            encoding="utf-8",
        )
        data = session_presence.snapshot(self.root)
        self.assertFalse(data["available"])
        self.assertIn("not a git repository", data["reason"])
        self.assertEqual(data["records"], [])


if __name__ == "__main__":
    unittest.main()
