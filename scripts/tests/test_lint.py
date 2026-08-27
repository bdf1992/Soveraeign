from __future__ import annotations

from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import io
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import lint  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]


def run_lint_over(files: dict[str, bytes]) -> tuple[int, str]:
    """Run the real lint entry point over a throwaway tree and capture its report.

    The CRLF blind spot lived in how main() read the file, not in check_text, so a
    defeating case only counts if it goes through the reader.
    """
    with TemporaryDirectory() as raw:
        root = Path(raw).resolve()
        for name, payload in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        buffer = io.StringIO()
        with patch.object(lint, "ROOT", root), redirect_stdout(buffer):
            code = lint.main()
        return code, buffer.getvalue()


class ReaderPreservesLineEndings(unittest.TestCase):
    def test_crlf_file_is_a_defect(self) -> None:
        code, report = run_lint_over({"note.md": b"first\r\nsecond\r\n"})
        self.assertEqual(code, 1)
        self.assertIn("note.md: CRLF line endings", report)

    def test_lone_cr_file_is_a_defect(self) -> None:
        code, report = run_lint_over({"note.md": b"first\rsecond\n"})
        self.assertEqual(code, 1)
        self.assertIn("note.md: CRLF line endings", report)

    def test_lf_file_passes(self) -> None:
        code, report = run_lint_over({"note.md": b"first\nsecond\n"})
        self.assertEqual(code, 0)
        self.assertIn("PASS: repository hygiene", report)

    def test_missing_final_newline_still_reported(self) -> None:
        code, report = run_lint_over({"note.md": b"first\nsecond"})
        self.assertEqual(code, 1)
        self.assertIn("note.md: missing final newline", report)


class ReaderRefusesUndecodableText(unittest.TestCase):
    def test_non_utf8_file_is_a_defect_not_a_traceback(self) -> None:
        code, report = run_lint_over({"note.md": b"caf\xe9\n"})
        self.assertEqual(code, 1)
        self.assertIn("note.md: not valid UTF-8", report)


class RepositoryTraversal(unittest.TestCase):
    def test_skipped_trees_are_pruned_before_walk_descends(self) -> None:
        root = Path("/synthetic-repository")
        kept_dirs: list[str] = []

        def fake_walk(start: Path, topdown: bool = True):
            self.assertEqual(start, root)
            self.assertTrue(topdown)
            dirs = [".git", "visible", ".local", "worktrees"]
            yield str(root), dirs, ["root.md"]
            kept_dirs.extend(dirs)
            if ".git" in dirs:
                yield str(root / ".git"), [], ["secret.md"]
            if "visible" in dirs:
                yield str(root / "visible"), [], ["child.py"]
            if ".local" in dirs:
                yield str(root / ".local"), [], ["capture.md"]
            # A whole checkout of this repository, as `.claude/worktrees/` holds. Its
            # copy of an already-linted module must not enter the population twice.
            if "worktrees" in dirs:
                yield str(root / "worktrees"), [], ["child.py"]

        with patch.object(lint, "ROOT", root), patch.object(lint.os, "walk", fake_walk):
            paths = lint.repository_text_files()

        self.assertEqual(kept_dirs, ["visible"])
        self.assertEqual(paths, [root / "root.md", root / "visible" / "child.py"])


class RepositoryTreeHoldsTheInvariant(unittest.TestCase):
    def test_no_repository_text_file_carries_a_cr_byte(self) -> None:
        """Checked by byte scan, independently of the lint rule the scan protects."""
        with patch.object(lint, "ROOT", REPO_ROOT):
            paths = lint.repository_text_files()
        self.assertGreater(len(paths), 0)
        carrying = [
            path.relative_to(REPO_ROOT).as_posix()
            for path in paths
            if b"\r" in path.read_bytes()
        ]
        self.assertEqual(carrying, [])

    def test_gitattributes_pins_lf_checkout(self) -> None:
        text = (REPO_ROOT / ".gitattributes").read_bytes().decode("utf-8")
        self.assertIn("* text=auto eol=lf", text)
        self.assertIn("lineage/** -text", text)


if __name__ == "__main__":
    unittest.main()


class DecisionNumbers(unittest.TestCase):
    """One decision number, one record. Two branches minting the next free number
    independently is how four collisions reached the tree before this check existed."""

    def _over(self, names: list[str]) -> list[str]:
        with TemporaryDirectory() as raw:
            directory = Path(raw)
            for name in names:
                (directory / name).write_bytes(b"# a record\n")
            return lint.check_decision_numbers(directory)

    def test_distinct_numbers_pass(self):
        self.assertEqual(self._over(["0001-a.md", "0002-b.md", "0057-c.md"]), [])

    def test_a_repeated_number_is_reported(self):
        """The defeating case: the exact shape that reached the tree, two different
        records both numbered 0027."""
        defects = self._over(["0027-board-management-role.md", "0027-local-model-adapter.md"])
        self.assertEqual(len(defects), 1)
        self.assertIn("number 0027 is carried by 2 records", defects[0])
        self.assertIn("0027-board-management-role.md", defects[0])
        self.assertIn("0027-local-model-adapter.md", defects[0])

    def test_every_repeated_number_is_reported_not_only_the_first(self):
        defects = self._over(["0027-a.md", "0027-b.md", "0042-c.md", "0042-d.md"])
        self.assertEqual(len(defects), 2)

    def test_a_number_carried_three_times_says_three(self):
        defects = self._over(["0051-a.md", "0051-b.md", "0051-c.md"])
        self.assertIn("carried by 3 records", defects[0])

    def test_files_that_are_not_numbered_records_are_ignored(self):
        self.assertEqual(self._over(["README.md", "0001-a.md"]), [])

    def test_the_real_decisions_directory_carries_no_duplicate(self):
        """The regression guard: this is the state the reconciliation left behind."""
        self.assertEqual(lint.check_decision_numbers(REPO_ROOT / "decisions"), [])


class ModuleSizeLimitIsEnforced(unittest.TestCase):
    """The 300-line rule, proved with an empty debt registry.

    An empty KNOWN_MODULE_DEBT should mean no production module is over the limit.
    It could equally mean the limit stopped being measured, and nothing in the tree
    distinguishes those two once the last entry is removed. These cases fix that:
    the registry is patched empty and a synthetic over-limit module must still be
    reported as a defect, not as named debt.
    """

    def _module_of(self, lines: int) -> bytes:
        body = "from __future__ import annotations\n" + "value = 1\n" * (lines - 1)
        return body.encode("utf-8")

    def test_a_module_at_the_limit_passes(self) -> None:
        with patch.dict(lint.KNOWN_MODULE_DEBT, {}, clear=True):
            code, report = run_lint_over(
                {"scripts/at_limit.py": self._module_of(lint.MAX_PRODUCTION_LINES)}
            )
        self.assertEqual(code, 0, report)
        self.assertNotIn("exceeds production limit", report)

    def test_an_unregistered_module_one_line_over_is_a_defect(self) -> None:
        """The defeating case: one line over, no debt entry, empty registry."""
        with patch.dict(lint.KNOWN_MODULE_DEBT, {}, clear=True):
            code, report = run_lint_over(
                {"scripts/over_limit.py": self._module_of(lint.MAX_PRODUCTION_LINES + 1)}
            )
        self.assertEqual(code, 1, report)
        self.assertIn(
            f"scripts/over_limit.py: {lint.MAX_PRODUCTION_LINES + 1} lines exceeds "
            f"production limit {lint.MAX_PRODUCTION_LINES}",
            report,
        )
        self.assertNotIn("KNOWN DEBT", report)

    def test_a_registered_module_over_the_limit_is_named_debt_not_a_defect(self) -> None:
        """The warning path stays reachable, so an empty registry is a fact about the
        tree rather than a disabled rule."""
        entry = {"scripts/over_limit.py": "synthetic entry for this fixture"}
        with patch.dict(lint.KNOWN_MODULE_DEBT, entry, clear=True):
            code, report = run_lint_over(
                {"scripts/over_limit.py": self._module_of(lint.MAX_PRODUCTION_LINES + 1)}
            )
        self.assertEqual(code, 0, report)
        self.assertIn("KNOWN DEBT: scripts/over_limit.py", report)
        self.assertNotIn("exceeds production limit", report)

    def test_a_test_module_over_the_limit_is_not_production(self) -> None:
        with patch.dict(lint.KNOWN_MODULE_DEBT, {}, clear=True):
            code, report = run_lint_over(
                {"scripts/tests/test_big.py": self._module_of(lint.MAX_PRODUCTION_LINES + 1)}
            )
        self.assertEqual(code, 0, report)
