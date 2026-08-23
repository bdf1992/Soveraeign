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
