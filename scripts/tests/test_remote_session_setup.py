"""Cases for the bootstrap that configures a remote container's ~/.claude.

This script edits files it did not write, in a directory shared with whatever
else the host put there, so what these press is loss rather than function. Every
defeating case here is a defect a witness found first: a substring test that
deleted a sibling clone's hook entries and reported success, a malformed settings
file that lost every key, an ownership test that inferred authorship from a
file's shape and withheld the backup the operator needed, and a guarantee that
held for the settings file while the output style beside it was overwritten with
no copy kept.
"""

from __future__ import annotations

from pathlib import Path
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP = ROOT / ".claude" / "bootstrap"

sys.path.insert(0, str(BOOTSTRAP))
import remote_session_setup as boot  # noqa: E402
import user_settings as store  # noqa: E402

WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
         7: "seven", 8: "eight", 9: "nine", 10: "ten", 11: "eleven", 12: "twelve"}


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
    (repo / ".claude" / "output-styles" / "communications.md").write_text(
        "repository style", encoding="utf-8")
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

    def seed(self, text: str) -> None:
        self.settings.write_text(text, encoding="utf-8")

    def run_bootstrap(self, repo: Path | None = None) -> dict:
        """Run main() itself against a private HOME, so no case can drift from it."""
        repo = repo or self.repo
        env = {"HOME": str(self.user.parent), "CLAUDE_CODE_REMOTE": "true"}
        old_env = {k: os.environ.get(k) for k in env}
        old_argv = sys.argv
        os.environ.update(env)
        sys.argv = [str(BOOTSTRAP / "remote_session_setup.py"), str(repo)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, boot.main())
        finally:
            sys.argv = old_argv
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        return json.loads(self.settings.read_text(encoding="utf-8"))


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
        self.assertTrue(boot.ours(boot.hook_entries(self.repo, "SessionStart")[0], link))


class Ownership(Sandbox):
    """What is kept before a file is replaced, and what is not."""

    def test_an_operator_file_shaped_like_ours_is_still_backed_up(self):
        """The defeating case: authorship inferred from shape, and loss followed."""
        script = str(self.repo / ".claude" / "hooks" / "console_session.py")
        theirs = {"outputStyle": boot.STYLE_NAME, "hooks": {"SessionStart": [{"hooks": [
            {"type": "command", "command": script, "args": [script, "start"], "timeout": 300}]}]}}
        self.seed(json.dumps(theirs))
        kept = store.keep_aside(self.user, "settings.json", self.settings)
        self.assertIsNotNone(kept)
        self.assertEqual(theirs, json.loads((self.user / kept).read_text(encoding="utf-8")))

    def test_an_operator_output_style_is_kept_before_it_is_replaced(self):
        """The defeating case: the guarantee held for settings.json and not beside it.

        install_styles copied over the operator's own style with no backup, on
        every session start, while the README said nothing was replaced without
        a copy kept.
        """
        styles = self.user / "output-styles"
        styles.mkdir()
        theirs = "operator's own style, irreplaceable"
        (styles / "communications.md").write_text(theirs, encoding="utf-8")
        self.run_bootstrap()
        kept = [p for p in styles.glob("communications.md.*") if theirs in
                p.read_text(encoding="utf-8")]
        self.assertEqual(1, len(kept))
        self.assertEqual("repository style",
                         (styles / "communications.md").read_text(encoding="utf-8"))

    def test_no_file_it_replaces_is_replaced_without_a_copy_kept(self):
        """The broad sentence, over both kinds of file this tool writes."""
        styles = self.user / "output-styles"
        styles.mkdir()
        (styles / "communications.md").write_text("operator style", encoding="utf-8")
        self.seed(json.dumps({"model": "operator settings"}))
        self.run_bootstrap()
        for directory, needle in ((self.user, "operator settings"),
                                  (styles, "operator style")):
            kept = [q for q in directory.glob("*.sov-bootstrap-backup*")
                    if needle in q.read_text(encoding="utf-8")]
            self.assertEqual(1, len(kept), needle)

    def test_bytes_this_tool_wrote_are_not_kept_again(self):
        self.run_bootstrap()
        self.assertTrue(store.is_own_output(self.user, "settings.json", self.settings))
        self.assertIsNone(store.keep_aside(self.user, "settings.json", self.settings))

    def test_an_edit_to_our_own_output_is_kept(self):
        self.run_bootstrap()
        edited = json.loads(self.settings.read_text(encoding="utf-8"))
        edited["model"] = "theirs"
        self.settings.write_text(json.dumps(edited), encoding="utf-8")
        self.assertIsNotNone(store.keep_aside(self.user, "settings.json", self.settings))

    def test_bytes_already_held_aside_are_not_held_again(self):
        """Without this the aside copies grow at every session start, unbounded."""
        self.seed('{"model": "theirs"}')
        self.assertIsNotNone(store.keep_aside(self.user, "settings.json", self.settings))
        self.assertIsNone(store.keep_aside(self.user, "settings.json", self.settings))
        self.assertEqual(1, len(list(self.user.glob("settings.json.sov-bootstrap-backup*"))))

    def test_a_name_already_taken_is_never_reused(self):
        """Deterministic form of the same-second collision: the stamp cannot vary."""
        taken = self.user / "settings.json.aside"
        taken.write_text("first", encoding="utf-8")
        self.assertNotEqual(taken, store.free_name(self.settings, "settings.json.aside"))

    def test_a_second_unparsed_copy_does_not_displace_the_first(self):
        self.seed('{"model": "first", ')
        first = store.keep_aside(self.user, "settings.json", self.settings, False)
        self.seed('{"model": "second", ')
        second = store.keep_aside(self.user, "settings.json", self.settings, False)
        self.assertNotEqual(first, second)
        self.assertIn("first", (self.user / first).read_text(encoding="utf-8"))
        self.assertIn("second", (self.user / second).read_text(encoding="utf-8"))

    def test_a_settings_path_that_is_not_a_file_is_reported_as_unkeepable(self):
        self.settings.mkdir()
        self.assertIsNone(store.keep_aside(self.user, "settings.json", self.settings, False))


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

    def test_a_file_that_does_not_parse_is_reported_as_not_intact(self):
        """The intact flag is what routes the bytes to safety; nothing graded it."""
        self.seed('{"model": "keep-me", ')
        self.assertEqual(({}, False), store.read_settings(self.settings))

    def test_a_file_that_does_not_parse_is_kept_rather_than_discarded(self):
        self.seed('{"model": "keep-me", ')
        kept = store.keep_aside(self.user, "settings.json", self.settings, False)
        self.assertIn("keep-me", (self.user / kept).read_text(encoding="utf-8"))

    def test_json_that_is_not_an_object_is_not_treated_as_intact(self):
        for text in ("[1, 2]", '"hello"', "null", "123"):
            self.seed(text)
            self.assertEqual(({}, False), store.read_settings(self.settings), text)


class Replacement(Sandbox):
    """How a file is written, not what goes in it."""

    def modes(self):
        old = os.umask(0)
        self.addCleanup(os.umask, old)

    def test_the_file_mode_survives_the_replacement(self):
        """os.replace from a fresh temporary widened 0600 to 0644."""
        self.modes()
        for mode in (0o600, 0o640, 0o644):
            self.seed("{}")
            os.chmod(self.settings, mode)
            store.write_private(self.settings, "{}\n")
            self.assertEqual(mode, self.settings.stat().st_mode & 0o777, oct(mode))

    def test_the_temporary_is_never_more_readable_than_the_target(self):
        """The docstring promised this window; write_text left it world-readable."""
        self.modes()
        self.seed("{}")
        os.chmod(self.settings, 0o600)
        seen, real = [], os.chmod

        def spy(path, mode):
            seen.append(Path(path).stat().st_mode & 0o777)
            real(path, mode)

        store.os.chmod = spy
        try:
            store.write_private(self.settings, "{}\n")
        finally:
            store.os.chmod = real
        self.assertEqual([0o600], seen)

    def test_the_target_is_replaced_rather_than_truncated_in_place(self):
        """A concurrent reader sees the old file or the new one, never a half."""
        self.seed("{}")
        before = self.settings.stat().st_ino
        store.write_private(self.settings, "{}\n")
        self.assertNotEqual(before, self.settings.stat().st_ino)

    def test_a_failed_replacement_leaves_no_temporary_and_no_damage(self):
        self.seed('{"keep": true}')
        real = os.replace

        def boom(*_args):
            raise OSError("replace refused")

        store.os.replace = boom
        try:
            with self.assertRaises(OSError):
                store.write_private(self.settings, "{}\n")
        finally:
            store.os.replace = real
        self.assertEqual('{"keep": true}', self.settings.read_text(encoding="utf-8"))
        self.assertEqual([], sorted(self.user.glob("settings.json.tmp-*")))

    def test_the_state_file_is_readable_only_by_its_owner(self):
        self.modes()
        store.save_state(self.user, {"settings.json": "sha256:x"})
        self.assertEqual(0o600, store.state_path(self.user).stat().st_mode & 0o777)

    def test_a_symlinked_settings_file_is_written_through(self):
        real = self.user / "elsewhere.json"
        real.write_text("{}", encoding="utf-8")
        self.settings.symlink_to(real)
        self.run_bootstrap()
        self.assertTrue(self.settings.is_symlink())
        self.assertIn("outputStyle", json.loads(real.read_text(encoding="utf-8")))

    def test_a_repository_with_no_styles_still_registers_hooks(self):
        shutil.rmtree(self.repo / ".claude" / "output-styles")
        self.assertEqual((0, []), boot.install_styles(self.repo, self.user))
        self.assertTrue(boot.hook_entries(self.repo, "SessionStart"))

    def test_a_hook_script_that_is_not_there_is_not_registered(self):
        (self.repo / ".claude" / "hooks" / "stranded_work.py").unlink()
        names = json.dumps(boot.hook_entries(self.repo, "SessionStart"))
        self.assertNotIn("stranded_work.py", names)
        self.assertIn("console_session.py", names)


class TheStateFile(Sandbox):
    """This tool's own record is still a file it writes into somebody's directory."""

    def test_it_is_never_more_readable_than_its_final_mode(self):
        """Path.write_text created it at 0666 & ~umask, the bug this module names."""
        self.modes()
        seen, real = [], os.chmod

        def spy(path, mode):
            seen.append(Path(path).stat().st_mode & 0o777)
            real(path, mode)

        store.os.chmod = spy
        try:
            store.save_state(self.user, {"settings.json": "sha256:x"})
        finally:
            store.os.chmod = real
        self.assertTrue(seen, "no mode was set at all")
        self.assertTrue(all(mode == 0o600 for mode in seen), [oct(m) for m in seen])
        self.assertEqual(0o600, store.state_path(self.user).stat().st_mode & 0o777)

    def test_the_state_file_is_not_backed_up(self):
        """It is this tool's own record, so it is the one file with no copy kept."""
        self.run_bootstrap()
        store.save_state(self.user, {"settings.json": "sha256:changed"})
        self.assertEqual([], sorted(self.user.glob(".sov-bootstrap-state.json.*")))

    def test_keys_this_tool_did_not_write_are_carried_forward(self):
        store.state_path(self.user).write_text(
            json.dumps({"operator": "notes", "written": {}}), encoding="utf-8")
        store.save_state(self.user, {"settings.json": "sha256:x"})
        document = json.loads(store.state_path(self.user).read_text(encoding="utf-8"))
        self.assertEqual("notes", document["operator"])
        self.assertIn("settings.json", document["written"])

    def modes(self):
        old = os.umask(0)
        self.addCleanup(os.umask, old)


class BytesNotText(Sandbox):
    """Files are compared as bytes; decoding them cost two files."""

    def test_a_file_that_is_not_utf8_is_held_aside_only_once(self):
        """Without a byte digest its copies grew at every session start."""
        self.settings.write_bytes(b"\xff\xfe operator binary \x00")
        for _ in range(4):
            store.keep_aside(self.user, "settings.json", self.settings)
        self.assertEqual(1, len(list(self.user.glob("settings.json.sov-bootstrap-backup*"))))

    def test_a_crlf_file_is_not_mistaken_for_its_lf_twin(self):
        """Reading as text folds CRLF into LF, and the CRLF bytes were destroyed."""
        self.settings.write_bytes(b'{"a": 1}\n')
        first = store.keep_aside(self.user, "settings.json", self.settings)
        self.settings.write_bytes(b'{"a": 1}\r\n')
        second = store.keep_aside(self.user, "settings.json", self.settings)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertNotEqual(first, second)


class TheUnparsedPath(Sandbox):
    """Reachable only through main(), where the intact flag is wired."""

    def test_a_run_against_an_unparseable_file_keeps_its_bytes(self):
        """Deleting main()'s intact argument passed every case before this one."""
        self.seed('{"model": "keep-me", ')
        self.run_bootstrap()
        kept = [p for p in self.user.glob("settings.json.unparsed*")
                if "keep-me" in p.read_text(encoding="utf-8")]
        self.assertEqual(1, len(kept))
        self.assertIn("outputStyle", json.loads(self.settings.read_text(encoding="utf-8")))

    def test_the_unparsed_copy_is_named_apart_from_the_backup(self):
        """A stem swap to the plain backup name passed every case before this one."""
        self.seed("not json at all")
        kept = store.keep_aside(self.user, "settings.json", self.settings, False)
        self.assertTrue(kept.startswith("settings.json.unparsed"), kept)


class HostileSettings(Sandbox):
    """Shapes that used to stop the run without saying so."""

    def test_a_hooks_value_that_is_not_an_object_does_not_stop_the_run(self):
        """It raised out of merge_hooks and was swallowed: no hooks, no message, ever."""
        for shape in ('"none"', "[{}]", "3"):
            self.seed('{"model": "opus", "hooks": ' + shape + "}")
            result = self.run_bootstrap()
            self.assertIn("SessionStart", result["hooks"], shape)

    def test_a_style_that_cannot_be_read_does_not_cost_the_session_its_hooks(self):
        (self.repo / ".claude" / "output-styles" / "broken.md").mkdir()
        result = self.run_bootstrap()
        self.assertIn("SessionStart", result["hooks"])
        self.assertTrue((self.user / "output-styles" / "communications.md").is_file())

    def test_a_symlinked_style_is_written_through(self):
        styles = self.user / "output-styles"
        styles.mkdir()
        real = self.user / "elsewhere.md"
        real.write_text("operator style", encoding="utf-8")
        (styles / "communications.md").symlink_to(real)
        self.run_bootstrap()
        self.assertTrue((styles / "communications.md").is_symlink())
        self.assertEqual("repository style", real.read_text(encoding="utf-8"))


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


class AsideCopyPermissions(Sandbox):
    """A backup of a secrets file is a secrets file."""

    def test_the_aside_copy_does_not_widen_the_mode_of_what_it_copies(self):
        """shutil.copyfile creates at 0666 & ~umask and never narrows again.

        ~/.claude/settings.json holds apiKeyHelper and env. A 0600 original left
        a world-readable copy of itself beside it, permanently.
        """
        old = os.umask(0)
        self.addCleanup(os.umask, old)
        for mode in (0o600, 0o640, 0o604):
            self.seed(json.dumps({"env": {"KEY": f"secret-{mode}"}}))
            os.chmod(self.settings, mode)
            kept = store.keep_aside(self.user, "settings.json", self.settings)
            self.assertEqual(mode, (self.user / kept).stat().st_mode & 0o777, oct(mode))


class HostileUserDirectory(Sandbox):
    """Whatever is already in ~/.claude, the session still gets configured or told."""

    def test_a_file_where_the_styles_directory_belongs_does_not_stop_the_run(self):
        (self.user / "output-styles").write_text("not a directory", encoding="utf-8")
        result = self.run_bootstrap()
        self.assertIn("SessionStart", result["hooks"])

    def promptly(self, call):
        """Run a call that must not block, failing rather than hanging the suite."""
        done = []
        worker = threading.Thread(target=lambda: done.append(call()), daemon=True)
        worker.start()
        worker.join(5)
        self.assertFalse(worker.is_alive(), "the call blocked instead of returning")
        return done[0]

    def test_a_fifo_settings_file_does_not_block_the_run(self):
        """Reading a FIFO hung the tool until the host killed the hook."""
        os.mkfifo(self.settings)
        self.assertEqual(({}, False), self.promptly(lambda: store.read_settings(self.settings)))
        self.assertIsNone(self.promptly(lambda: store.digest_of(self.settings)))

    def test_a_target_that_is_not_a_regular_file_is_refused_rather_than_replaced(self):
        """A device node was silently replaced by a regular file, nothing kept."""
        os.mkfifo(self.settings)
        with self.assertRaises(OSError):
            store.write_private(self.settings, "{}\n")
        self.assertFalse(self.settings.is_file())

    def test_a_third_distinct_file_gets_its_own_aside_name(self):
        for content in ('{"a": 1}', '{"b": 2}', '{"c": 3}'):
            self.seed(content)
            store.keep_aside(self.user, "settings.json", self.settings)
        kept = sorted(self.user.glob("settings.json.sov-bootstrap-backup*"))
        self.assertEqual(3, len(kept))
        self.assertEqual(3, len({p.read_text(encoding="utf-8") for p in kept}))

    def test_bytes_already_held_under_an_indexed_name_are_not_held_again(self):
        """Alternating contents grew without bound when the glob missed indexes."""
        for content in ('{"a": 1}', '{"b": 2}', '{"a": 1}', '{"b": 2}'):
            self.seed(content)
            store.keep_aside(self.user, "settings.json", self.settings)
        self.assertEqual(2, len(list(self.user.glob("settings.json.sov-bootstrap-backup*"))))

    def test_the_same_unparsed_bytes_are_kept_once(self):
        """The stable stem exists so this check can see its own siblings."""
        for _ in range(4):
            self.seed("not json at all")
            store.keep_aside(self.user, "settings.json", self.settings, False)
        self.assertEqual(1, len(list(self.user.glob("settings.json.unparsed*"))))


class TheGuardsEffect(Sandbox):
    """The predicate was graded; what it prevents was not."""

    def test_a_run_that_is_not_remote_writes_nothing(self):
        env = {"HOME": str(self.user.parent)}
        old_home = os.environ.get("HOME")
        old_remote = os.environ.pop("CLAUDE_CODE_REMOTE", None)
        old_argv = sys.argv
        os.environ.update(env)
        sys.argv = ["remote_session_setup.py", str(self.repo)]
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, boot.main())
        finally:
            sys.argv = old_argv
            if old_home is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = old_home
            if old_remote is not None:
                os.environ["CLAUDE_CODE_REMOTE"] = old_remote
        self.assertFalse(self.settings.exists())
        self.assertFalse((self.user / "output-styles").exists())


class EntryShapes(Sandbox):
    """Hook entries arrive in shapes nobody promised."""

    def test_an_entry_naming_a_repository_script_as_command_is_ours(self):
        script = str(self.repo / ".claude" / "hooks" / "console_session.py")
        self.assertTrue(boot.ours({"hooks": [{"type": "command", "command": script}]}, self.repo))

    def test_an_entry_path_is_resolved_before_it_is_compared(self):
        """A link from outside the repository still names a script inside it."""
        link = self.base / "linked-hooks"
        link.symlink_to(self.repo / ".claude" / "hooks")
        script = str(link / "console_session.py")
        self.assertFalse(Path(script).is_relative_to(self.repo), "the case proves nothing")
        self.assertTrue(boot.ours({"hooks": [{"command": script}]}, self.repo))

    def test_a_per_event_value_that_is_not_a_list_does_not_stop_the_run(self):
        self.seed(json.dumps({"hooks": {"SessionStart": "nope", "Stop": "keep"}}))
        result = self.run_bootstrap()
        self.assertTrue(result["hooks"]["SessionStart"])
        self.assertEqual("keep", result["hooks"]["Stop"])


# Each sentence in .claude/README.md that promises behaviour, and the case that
# demonstrates it. Reword or delete the sentence and the first case below fails;
# delete or rename the case and the second one does.
CLAIMS = {
    "It writes nothing unless `CLAUDE_CODE_REMOTE` is `true`":
        "TheGuardsEffect.test_a_run_that_is_not_remote_writes_nothing",
    "It carries forward every key and every hook entry in an existing":
        "ForeignSettings.test_foreign_keys_and_events_survive",
    "No file it replaces is replaced without a copy kept beside it":
        "Ownership.test_no_file_it_replaces_is_replaced_without_a_copy_kept",
    "never reusing a name already taken":
        "Ownership.test_a_name_already_taken_is_never_reused",
    "never keeping bytes already held beside the file":
        "HostileUserDirectory.test_bytes_already_held_under_an_indexed_name_are_not_held_again",
    "Files are compared as bytes":
        "BytesNotText.test_a_crlf_file_is_not_mistaken_for_its_lf_twin",
    "a file it cannot decode still deduplicates":
        "BytesNotText.test_a_file_that_is_not_utf8_is_held_aside_only_once",
    "its bytes are kept under `settings.json.unparsed`":
        "TheUnparsedPath.test_a_run_against_an_unparseable_file_keeps_its_bytes",
    "A copy carries the mode of what it copied":
        "AsideCopyPermissions.test_the_aside_copy_does_not_widen_the_mode_of_what_it_copies",
    "A path that is not a regular file is refused rather than replaced":
        "HostileUserDirectory.test_a_target_that_is_not_a_regular_file_is_refused_rather_"
        "than_replaced",
    "and never read":
        "HostileUserDirectory.test_a_fifo_settings_file_does_not_block_the_run",
    "Keys in it that this tool did not write are carried forward":
        "TheStateFile.test_keys_this_tool_did_not_write_are_carried_forward",
    "and it is not backed up":
        "TheStateFile.test_the_state_file_is_not_backed_up",
    "It knows what it wrote by recording each write's digest in that state file":
        "Ownership.test_bytes_this_tool_wrote_are_not_kept_again",
    "A file that is a symlink is written through rather than replaced":
        "Replacement.test_a_symlinked_settings_file_is_written_through",
    "It leaves out the `PreToolUse` and `PostToolUse` path-claim hooks":
        "DeclaredRoster.test_no_path_claim_hook_is_registered",
    "It decides what belongs to this repository by path component, not by substring":
        "SiblingRepositories.test_a_sibling_whose_name_extends_this_one_keeps_its_hooks",
}


class ThePromisedBehaviour(unittest.TestCase):
    """Every guarantee the README makes names the case that demonstrates it.

    Three of the five refusals this module exists because of were a sentence
    here that the code did not support, and nothing graded the sentence. A
    clarity review does not and never claimed to: it keeps a claim intact
    through a rewrite, it does not test the claim. This is what tests it.

    What it reaches: a sentence that is reworded or deleted while the behaviour
    stays, and a case that is deleted or renamed while the sentence stays. What
    it does not reach: a sentence whose named case is weak. Only mutating the
    implementation grades that, and the record of which mutations were run and
    caught lives in the commit messages, not here.
    """

    def readme(self) -> str:
        text = (ROOT / ".claude" / "README.md").read_text(encoding="utf-8")
        return " ".join(text.split())

    def test_every_claim_is_stated_in_the_readme(self):
        text = self.readme()
        for fragment in CLAIMS:
            self.assertIn(" ".join(fragment.split()), text, fragment)

    def test_every_claim_names_a_case_that_exists(self):
        for fragment, case in CLAIMS.items():
            owner_name, method = case.rsplit(".", 1)
            owner = globals().get(owner_name)
            self.assertIsNotNone(owner, f"{fragment!r} names missing class {owner_name}")
            self.assertTrue(callable(getattr(owner, method, None)),
                            f"{fragment!r} names missing case {case}")


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
        self.assertIn(total, WORDS, f"no word for {total}; extend WORDS")
        readme = (ROOT / ".claude" / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"registers {WORDS[total]} entries", readme)

    def test_no_path_claim_hook_is_registered(self):
        self.assertNotIn("PreToolUse", boot.HOOKS)
        self.assertNotIn("PostToolUse", boot.HOOKS)


if __name__ == "__main__":
    unittest.main()
