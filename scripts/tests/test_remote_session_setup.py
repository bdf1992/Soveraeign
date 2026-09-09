"""Cases for the bootstrap that configures a remote container's ~/.claude.

This script edits a file it did not write, in a directory shared with whatever
else the host put there, so what these press is loss rather than function. The
substring test that shipped first deleted a sibling repository's hook entries and
reported success; a malformed settings file lost every key the same way. Both are
here as defeating cases, along with the guard that keeps the whole thing off a
workstation.
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / ".claude" / "bootstrap" / "remote_session_setup.py"

sys.path.insert(0, str(BOOTSTRAP.parent))
import remote_session_setup as boot  # noqa: E402


def fake_repo(base: Path, name: str) -> Path:
    """Build the smallest tree the bootstrap will accept as a repository."""
    repo = base / name
    (repo / ".claude" / "hooks").mkdir(parents=True)
    (repo / ".claude" / "bootstrap").mkdir(parents=True)
    (repo / ".claude" / "output-styles").mkdir(parents=True)
    for script, _mode, _timeout, _message in (
        boot.HOOKS["SessionStart"] + boot.HOOKS["SessionEnd"] + boot.HOOKS["UserPromptSubmit"]
    ):
        target = repo / ".claude" / (script if "/" in script else f"hooks/{script}")
        target.write_text("", encoding="utf-8")
    (repo / ".claude" / "output-styles" / "communications.md").write_text("x", encoding="utf-8")
    return repo


class Sandbox(unittest.TestCase):
    """Every case builds its own repository and its own user directory."""

    def setUp(self):
        self.base = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.repo = fake_repo(self.base, "Soveraeign")
        self.user = self.base / "home" / ".claude"
        self.user.mkdir(parents=True)
        self.settings = self.user / "settings.json"

    def run_bootstrap(self, repo: Path | None = None) -> dict:
        """Apply the merge the way main() does, without touching the real HOME."""
        repo = repo or self.repo
        current, intact = boot.read_settings(self.settings)
        boot.preserve(self.settings, current, intact, repo)
        current["outputStyle"] = boot.STYLE_NAME
        current["hooks"] = boot.merge_hooks(current.get("hooks") or {}, repo)
        boot.write_atomic(self.settings, json.dumps(current, indent=2) + "\n")
        return current


class SiblingRepositories(Sandbox):
    """A repository whose path is a string prefix of another is a different repository."""

    def test_a_sibling_whose_name_extends_this_one_keeps_its_hooks(self):
        """The defeating case: `Soveraeign-fork` is not inside `Soveraeign`.

        A substring test says it is, and deleted all four of the fork's entries
        while reporting success. This is trap T3 in CLAUDE.md, arriving through a
        path rather than a standing token.
        """
        fork = fake_repo(self.base, "Soveraeign-fork")
        self.run_bootstrap(fork)
        before = [e for e in json.loads(self.settings.read_text())["hooks"]["SessionStart"]]
        self.assertTrue(before, "the fork registered nothing, so the case proves nothing")

        after = self.run_bootstrap(self.repo)["hooks"]["SessionStart"]
        survivors = [e for e in after if boot.ours(e, fork)]
        self.assertEqual(len(before), len(survivors))

    def test_this_repository_replaces_only_its_own_entries(self):
        first = self.run_bootstrap()["hooks"]["SessionStart"]
        second = self.run_bootstrap()["hooks"]["SessionStart"]
        self.assertEqual(len(first), len(second))


class ForeignSettings(Sandbox):
    """What the host and the operator put in that file has to come back out."""

    def seed(self, text: str) -> None:
        self.settings.write_text(text, encoding="utf-8")

    def test_foreign_keys_and_events_survive(self):
        self.seed(json.dumps({
            "model": "opus",
            "permissions": {"allow": ["Bash(git status)"]},
            "hooks": {
                "SessionStart": [{"hooks": [{"type": "command", "command": "/host/theirs.sh"}]}],
                "Stop": [{"hooks": [{"type": "command", "command": "/host/stop.sh"}]}],
            },
        }))
        result = self.run_bootstrap()
        self.assertEqual("opus", result["model"])
        self.assertIn("permissions", result)
        self.assertIn("Stop", result["hooks"])
        kept = [e for e in result["hooks"]["SessionStart"] if not boot.ours(e, self.repo)]
        self.assertEqual(1, len(kept))

    def test_a_file_that_does_not_parse_is_kept_rather_than_discarded(self):
        """The defeating case: an unreadable object silently lost every key."""
        self.seed('{"model": "keep-me", ')
        boot.preserve(self.settings, *boot.read_settings(self.settings), self.repo)
        salvaged = list(self.user.glob("settings.json.unparsed-*"))
        self.assertEqual(1, len(salvaged))
        self.assertIn("keep-me", salvaged[0].read_text(encoding="utf-8"))

    def test_the_backup_is_not_taken_of_this_script_s_own_output(self):
        """A backup of our own previous run would read as the state before it."""
        self.run_bootstrap()
        current, intact = boot.read_settings(self.settings)
        self.assertTrue(boot.is_own_output(current, self.repo))
        self.assertIsNone(boot.preserve(self.settings, current, intact, self.repo))

    def test_a_foreign_file_is_backed_up_once(self):
        self.seed(json.dumps({"model": "opus"}))
        first = boot.preserve(self.settings, *boot.read_settings(self.settings), self.repo)
        self.assertIsNotNone(first)
        self.run_bootstrap()
        again = boot.preserve(self.settings, *boot.read_settings(self.settings), self.repo)
        self.assertIsNone(again)
        backup = json.loads((self.user / first).read_text(encoding="utf-8"))
        self.assertEqual({"model": "opus"}, backup)


class Guard(unittest.TestCase):
    """The one refusal that keeps this off a machine it has no business on."""

    def test_only_the_exact_declared_value_admits_a_write(self):
        import os

        for value, expected in (
            ("true", True), ("TRUE", True), ("True", True), (" true ", True),
            ("", False), ("false", False), ("1", False), ("yes", False),
        ):
            os.environ["CLAUDE_CODE_REMOTE"] = value
            self.assertEqual(expected, boot.is_remote(), value)
        os.environ.pop("CLAUDE_CODE_REMOTE", None)
        self.assertFalse(boot.is_remote())


class RepositoryResolution(unittest.TestCase):
    """Registered as a hook this is called with a mode word, not a path."""

    def test_a_mode_word_does_not_become_a_repository_path(self):
        self.assertEqual(ROOT, boot.resolve_repo("start"))

    def test_no_argument_resolves_from_the_script_s_own_location(self):
        self.assertEqual(ROOT, boot.resolve_repo(None))

    def test_a_real_repository_path_is_honoured(self):
        self.assertEqual(ROOT, boot.resolve_repo(str(ROOT)))


if __name__ == "__main__":
    unittest.main()
