"""Positive and defeating cases for the composed-surface command.

The command was transplanted with no test of its own, and the mutation scorer
graded it accordingly: every mutant survived. What it owns is small and worth
pinning exactly — where the page is written, whether the session source is read
at all, and that rendering never registers a session as a side effect.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_composed_surface  # noqa: E402


class ComposedSurfaceCommand(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.out = Path(self.tmp.name) / "nested" / "surface.html"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = sov_composed_surface.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_it_writes_the_page_where_it_was_told_and_reports_what_it_read(self) -> None:
        code, out, _ = self.run_main("--out", str(self.out), "--no-sessions")
        self.assertEqual(code, 0)
        self.assertTrue(self.out.exists(), "the parent directory was not created")
        page = self.out.read_text(encoding="utf-8")
        self.assertTrue(page.startswith("<!doctype html>"))
        counts = sov_composed_surface.sov_surface.surface()["counts"]
        self.assertIn(f"{counts['declared']} declared", out)
        self.assertIn(f"{counts['reachable']} reachable", out)
        self.assertIn(f"{counts['observed']} observed", out)

    def test_the_page_is_written_with_lf_endings_on_every_host(self) -> None:
        self.run_main("--out", str(self.out), "--no-sessions")
        self.assertNotIn(b"\r\n", self.out.read_bytes())

    def test_disabling_sessions_renders_an_unavailable_state_not_an_empty_one(self) -> None:
        code, out, _ = self.run_main("--out", str(self.out), "--no-sessions")
        self.assertEqual(code, 0)
        page = self.out.read_text(encoding="utf-8")
        self.assertIn("Sessions unavailable", page)
        self.assertIn("session projection disabled for this rendering", page)
        self.assertIn("0 live harness session(s)", out)
        self.assertNotIn("data-card=\"session\"", page)

    def test_rendering_alone_never_registers_a_session(self) -> None:
        """Presence must be created by an explicit action, never by looking."""
        calls: list[list[str]] = []
        original = sov_composed_surface.register

        def refuse(*args: object, **kwargs: object) -> tuple[bool, str]:
            calls.append(["register"])
            return True, "should not have been called"

        sov_composed_surface.register = refuse  # type: ignore[assignment]
        try:
            self.run_main("--out", str(self.out), "--no-sessions")
        finally:
            sov_composed_surface.register = original  # type: ignore[assignment]
        self.assertEqual(calls, [])

    def test_a_refused_registration_stops_the_render_and_says_so(self) -> None:
        original = sov_composed_surface.register

        def refuse(*args: object, **kwargs: object) -> tuple[bool, str]:
            return False, "the session CLI is absent"

        sov_composed_surface.register = refuse  # type: ignore[assignment]
        try:
            code, out, err = self.run_main(
                "--out", str(self.out), "--no-sessions", "--register-session"
            )
        finally:
            sov_composed_surface.register = original  # type: ignore[assignment]
        self.assertEqual(code, 1)
        self.assertIn("REFUSED", err)
        self.assertIn("the session CLI is absent", err)
        self.assertFalse(self.out.exists(), "a refused registration still wrote a page")
        self.assertEqual(out, "")

    def test_an_accepted_registration_is_reported_as_harness_and_renders(self) -> None:
        seen: list[dict[str, object]] = []
        original = sov_composed_surface.register

        def accept(root: Path, **kwargs: object) -> tuple[bool, str]:
            seen.append(dict(kwargs))
            return True, "registered through scripts/sov_session.py"

        sov_composed_surface.register = accept  # type: ignore[assignment]
        try:
            code, out, _ = self.run_main(
                "--out", str(self.out), "--no-sessions", "--register-session",
                "--session-name", "session-test", "--intent", "surface probe",
            )
        finally:
            sov_composed_surface.register = original  # type: ignore[assignment]
        self.assertEqual(code, 0)
        self.assertEqual(seen, [{"name": "session-test", "intent": "surface probe"}])
        self.assertIn("HARNESS: registered", out)
        self.assertTrue(self.out.exists())

    def test_the_default_output_stays_out_of_the_checked_in_tree(self) -> None:
        """The composed page is a view, not a source of authority."""
        default = sov_composed_surface.DEFAULT_OUT.relative_to(ROOT)
        self.assertEqual(default.parts[0], ".local")
        self.assertFalse(sov_composed_surface.DEFAULT_OUT.is_relative_to(ROOT / "docs"))

    def test_an_unread_session_source_is_never_counted_as_live(self) -> None:
        original = sov_composed_surface.snapshot
        sov_composed_surface.snapshot = lambda root: {  # type: ignore[assignment]
            "available": False, "source": "s", "reason": "unreadable",
            "sessions": [{"session": "ghost"}], "records": [], "held": {},
        }
        try:
            _, out, _ = self.run_main("--out", str(self.out))
        finally:
            sov_composed_surface.snapshot = original  # type: ignore[assignment]
        self.assertIn("0 live harness session(s)", out)
        self.assertIn("unreadable", self.out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
