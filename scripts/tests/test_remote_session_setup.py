"""Cases for the bootstrap that configures a remote container's ~/.claude.

This script edits a file it did not write, in a directory shared with whatever
else the host put there, so what these press is loss rather than function. Each
defeating case here is a defect that reached a witness first: a substring test
that deleted a sibling clone's hook entries and reported success, a malformed
settings file that lost every key, and an ownership test that inferred authorship
from the file's shape and so withheld the backup from the operator file that
needed it.
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / ".claude" / "bootstrap"

sys.path.insert(0, str(BOOTSTRAP))
import remote_session_setup as boot  # noqa: E402
import user_settings as store  # noqa: E402

WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
         6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten"}


def fake_repo(base: Path, name: str) -> Path:
    """Build the smallest tree the bootstrap will accept as a repository."""
    repo = base / name
    (repo / ".claude" / "hooks").mkdir(parents=True)
    (repo / ".claude" / "bootstrap").mkdir(parents=True)
    (repo / ".claude" / "output-styles").mkdir(parents=True)
    for script, _mode, _timeout, _message in (
        boot.HOOKS["SessionStart"] + boot.HOOKS["SessionEnd"] + boot.HOOKS["UserPromptSubmit"]
    ):
        (repo / ".claude" / (script if "/" in script else f"hooks/{script}")).write_text(
            "", encoding="utf-8")
    (repo / ".claude" / "output-styles" / "communications.md").write_text("x", encoding="utf-8")
    return repo


class Sandbox(unittest.TestCase):
    """Every case builds its own repository and its own user directory.

    The base is resolved. A temporary root reached through a symlink, which is
    where `/tmp` points on some hosts, made every entry read as foreign and the
    entries duplicate without bound.
    """

    def setUp(self):
        self.base = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.base, ignore_errors=True)
        self.repo = fake_repo(self.base, "Soveraeign")
        self.user = self.base / "home" / ".claude"
        self.user.mkdir(parents=True)
        self.settings = self.user / "settings.json"

    def run_bootstrap(self, repo: Path | None = None) -> dict:
        """Apply what main() applies, without touching the real HOME."""
        repo = repo or self.repo
        current, intact = store.read_settings(self.settings)
        store.preserve(self.settings, intact)
        boot.install_styles(repo, self.user / "output-styles")
        current["outputStyle"] = boot.STYLE_NAME
        current["hooks"] = boot.merge_hooks(current.get("hooks") or {}, repo)
        store.write_settings(self.settings, current)
        return current

    def seed(self, text: str) -> None:
        self.settings.write_text(text, encoding="utf-8")


class SiblingRepositories(Sandbox):
    """A repository whose path extends this one's is a different repository."""

    def test_a_sibling_whose_name_extends_this_one_keeps_its_hooks(self):
        """`Soveraeign-fork` is not inside `Soveraeign`.

        A substring test says it is, and deleted all four of the fork's entries
        while reporting success. Trap T3 in CLAUDE.md, reaching a path rather
        than a standing token.
        """
        fork = fake_repo(self.base, "Soveraeign-fork")
        self.run_bootstrap(fork)
        before = json.loads(self.settings.read_text())["hooks"]["SessionStart"]
        self.assertTrue(before, "the fork registered nothing, so the case proves nothing")

        after = self.run_bootstrap(self.repo)["hooks"]["SessionStart"]
        self.assertEqual(len(before), len([e for e in after if boot.ours(e, fork)]))

    def test_this_repository_replaces_only_its_own_entries(self):
        first = self.run_bootstrap()["hooks"]["SessionStart"]
        second = self.run_bootstrap()["hooks"]["SessionStart"]
        self.assertEqual(len(first), len(second))

    def test_a_root_reached_through_a_symlink_is_still_this_repository(self):
        link = self.base / "linked"
        link.symlink_to(self.repo)
        entry = boot.hook_entries(self.repo, "SessionStart")[0]
        self.assertTrue(boot.ours(entry, link))


class Ownership(Sandbox):
    """What is kept before the file is replaced, and what is not."""

    def test_an_operator_file_shaped_like_ours_is_still_backed_up(self):
        """The defeating case: authorship inferred from shape, and loss followed.

        A file that selects Communications and registers a hook pointing into
        this repository is not therefore ours. Judging it by shape withheld the
        backup, and the operator's own entry was deleted with no way back.
        """
        script = str(self.repo / ".claude" / "hooks" / "console_session.py")
        theirs = {"outputStyle": boot.STYLE_NAME, "hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": script, "args": [script, "start"], "timeout": 300}]}]}}
        self.seed(json.dumps(theirs))
        kept = store.preserve(self.settings, True)
        self.assertIsNotNone(kept)
        self.assertEqual(theirs, json.loads((self.user / kept).read_text(encoding="utf-8")))

    def test_bytes_this_tool_wrote_are_not_backed_up_again(self):
        self.run_bootstrap()
        self.assertTrue(store.is_own_output(self.settings))
        self.assertIsNone(store.preserve(self.settings, True))

    def test_an_edit_to_our_own_output_is_backed_up(self):
        self.run_bootstrap()
        edited = json.loads(self.settings.read_text(encoding="utf-8"))
        edited["model"] = "theirs"
        self.settings.write_text(json.dumps(edited), encoding="utf-8")
        self.assertFalse(store.is_own_output(self.settings))
        self.assertIsNotNone(store.preserve(self.settings, True))

    def test_a_name_already_taken_is_never_reused(self):
        """Deterministic form of the same-second collision: the stamp cannot vary."""
        taken = self.user / "settings.json.aside"
        taken.write_text("first", encoding="utf-8")
        self.assertNotEqual(taken, store.free_name(self.settings, "settings.json.aside"))

    def test_a_second_unparsed_copy_does_not_displace_the_first(self):
        self.seed('{"model": "first", ')
        first = store.preserve(self.settings, False)
        self.seed('{"model": "second", ')
        second = store.preserve(self.settings, False)
        self.assertNotEqual(first, second)
        self.assertIn("first", (self.user / first).read_text(encoding="utf-8"))
        self.assertIn("second", (self.user / second).read_text(encoding="utf-8"))

    def test_a_settings_path_that_is_not_a_file_is_reported_as_unkeepable(self):
        self.settings.mkdir()
        self.assertIsNone(store.preserve(self.settings, False))


class ForeignSettings(Sandbox):
    """What the host and the operator put in that file has to come back out."""

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
        self.assertEqual(
            1, len([e for e in result["hooks"]["SessionStart"] if not boot.ours(e, self.repo)]))

    def test_a_file_that_does_not_parse_is_kept_rather_than_discarded(self):
        self.seed('{"model": "keep-me", ')
        kept = store.preserve(self.settings, store.read_settings(self.settings)[1])
        self.assertIn("keep-me", (self.user / kept).read_text(encoding="utf-8"))

    def test_json_that_is_not_an_object_is_not_treated_as_intact(self):
        for text in ("[1, 2]", '"hello"', "null", "123"):
            self.seed(text)
            self.assertEqual(({}, False), store.read_settings(self.settings), text)


class Replacement(Sandbox):
    """How the file is written, not what goes in it."""

    def test_the_file_mode_survives_the_replacement(self):
        """os.replace from a fresh temporary widened 0600 to 0644."""
        self.seed("{}")
        os.chmod(self.settings, 0o600)
        store.write_settings(self.settings, {"a": 1})
        self.assertEqual(0o600, self.settings.stat().st_mode & 0o777)

    def test_the_target_is_replaced_rather_than_truncated_in_place(self):
        """A concurrent reader sees the old file or the new one, never a half.

        The inode is how that is observable: a rename gives the name a new one,
        an in-place write keeps it and passes through a truncated state.
        """
        self.seed("{}")
        before = self.settings.stat().st_ino
        store.write_settings(self.settings, {"a": 1})
        self.assertNotEqual(before, self.settings.stat().st_ino)

    def test_no_temporary_sibling_is_left_behind(self):
        store.write_settings(self.settings, {"a": 1})
        self.assertEqual([], sorted(self.user.glob("settings.json.tmp-*")))

    def test_a_planted_temporary_of_another_run_is_not_removed(self):
        planted = self.user / "settings.json.tmp-999999"
        planted.write_text("theirs", encoding="utf-8")
        store.write_settings(self.settings, {"a": 1})
        self.assertEqual("theirs", planted.read_text(encoding="utf-8"))

    def test_the_styles_are_installed(self):
        self.assertEqual(1, boot.install_styles(self.repo, self.user / "output-styles"))
        self.assertTrue((self.user / "output-styles" / "communications.md").is_file())

    def test_a_repository_with_no_styles_still_registers_hooks(self):
        shutil.rmtree(self.repo / ".claude" / "output-styles")
        self.assertEqual(0, boot.install_styles(self.repo, self.user / "output-styles"))
        self.assertTrue(boot.hook_entries(self.repo, "SessionStart"))


class Guard(unittest.TestCase):
    """The one refusal that keeps this off a machine it has no business on."""

    def test_only_the_exact_declared_value_admits_a_write(self):
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


class DeclaredRoster(unittest.TestCase):
    """The prose count is bound to the roster, so it cannot drift again."""

    def test_the_readme_states_the_number_of_entries_the_code_registers(self):
        """It said six while enumerating seven, and nothing graded the sentence."""
        total = sum(len(entries) for entries in boot.HOOKS.values())
        readme = (ROOT / ".claude" / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"registers {WORDS[total]} entries", readme)

    def test_no_path_claim_hook_is_registered(self):
        self.assertNotIn("PreToolUse", boot.HOOKS)
        self.assertNotIn("PostToolUse", boot.HOOKS)


if __name__ == "__main__":
    unittest.main()
