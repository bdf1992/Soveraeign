"""Prove the workflow reader refuses the shape that reached a landing, and passes the tree.

`scripts/sov_workflows.py` exists because `.claude/workflows/` was graded by nothing:
`.js` is in none of lint's suffixes, so about four thousand lines assembling every prompt
this repository sends an agent were unread. A repair on 2026-09-08 shipped `'a' + + 'b'`,
which parses cleanly and puts the string `NaN` inside a prompt; only a hand-run syntax
check stood between it and a landing.

Both readings are shown to fire and to stay quiet on the real tree, so the check is
neither vacuous nor a check that refuses everything. Passing establishes `BUILT`.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_workflows  # noqa: E402
from sovharness.lexer import unreadable  # noqa: E402

CLEAN = "const x = await agent('a prompt', { agentType: 'sov-witness' })\n"


def write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.write_bytes(text.encode("utf-8"))
    return path


class TheReaderMeasures(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def test_a_clean_workflow_carries_no_defect(self):
        self.assertEqual(sov_workflows.grade(write(self.root, "a.js", CLEAN)), [])

    def test_the_concatenation_that_yields_NaN_is_refused(self):
        """The shape that actually reached a landing in this repository."""
        path = write(self.root, "b.js", "const p = 'first ' + + 'second'\n")
        self.assertTrue(any("NaN" in defect for defect in sov_workflows.grade(path)))

    def test_crlf_is_refused_because_the_repository_pins_LF(self):
        path = self.root / "c.js"
        path.write_bytes(b"const x = 1\r\nconst y = 2\r\n")
        self.assertTrue(any("CRLF" in defect for defect in sov_workflows.grade(path)))

    def test_a_directory_with_no_workflow_refuses_rather_than_passing_vacuously(self):
        """A check that graded nothing must say so; silence is not a clean reading."""
        self.assertEqual(sov_workflows.main(["--root", str(self.root)]), 1)

    def test_a_clean_directory_passes(self):
        write(self.root, "a.js", CLEAN)
        self.assertEqual(sov_workflows.main(["--root", str(self.root)]), 0)

    def test_a_defective_directory_refuses(self):
        write(self.root, "a.js", CLEAN)
        write(self.root, "b.js", "const p = 'x' + + 'y'\n")
        self.assertEqual(sov_workflows.main(["--root", str(self.root)]), 1)


class TheRealTreeIsRead(unittest.TestCase):
    def test_every_shipped_workflow_is_graded_and_clean(self):
        paths = sorted((ROOT / ".claude" / "workflows").glob("*.js"))
        self.assertGreaterEqual(len(paths), 20, "the reader would be grading almost nothing")
        for path in paths:
            with self.subTest(workflow=path.name):
                self.assertEqual(sov_workflows.grade(path), [])

    def test_a_regex_literal_does_not_produce_a_false_defect(self):
        """The construction named as the reason three checks were withdrawn.

        The earlier form of this case asserted only that two byte-level greps stayed quiet
        on the loop, which was trivially true and guarded nothing: it would have stayed
        green with a bracket reader reintroduced, because it never ran one. It now asserts
        the lexer reads this file, which is the thing that was said to be impossible.
        """
        loop = ROOT / ".claude" / "workflows" / "sov-loop.js"
        text = loop.read_text(encoding="utf-8")
        self.assertIn('replace(/"/g', text,
                      "this case is vacuous without the construction it guards against")
        self.assertIsNone(unreadable(text))
        self.assertEqual(sov_workflows.grade(loop), [])

    def test_a_call_written_in_prose_does_not_produce_a_false_defect(self):
        """The other named defense: "judging agent(s)" inside a sentence."""
        backlog = ROOT / ".claude" / "workflows" / "sov-backlog.js"
        text = backlog.read_text(encoding="utf-8")
        self.assertIn("agent(s)", text,
                      "this case is vacuous without the construction it guards against")
        self.assertIsNone(unreadable(text))
        self.assertEqual(sov_workflows.grade(backlog), [])


class TheReadingIsLexicalAndSaysSo(unittest.TestCase):
    """Each defect the reader claims to see, shown on a file built to carry it.

    Two of these shapes were live in this repository while an earlier version of this
    check reported every workflow clean: an apostrophe closing a single-quoted string, and
    a string broken across raw newlines. A green suite asserted it.
    """

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def unread(self, source: str) -> str | None:
        return unreadable(source)

    def test_an_apostrophe_closing_a_string_is_caught(self):
        """sov-trust.js line 39 held exactly this, and shipped as clean."""
        found = self.unread("const p = 'This workflow's envelope is local' + x\n")
        self.assertIsNotNone(found)
        self.assertIn("not closed", found)

    def test_a_string_broken_across_raw_newlines_is_caught(self):
        """sov-coldstart.js held three of these."""
        found = self.unread('const p = \'a\' + "\n\n" + \'b\'\n')
        self.assertIsNotNone(found)

    def test_an_unbalanced_bracket_is_caught(self):
        self.assertIsNotNone(self.unread("const x = foo(1, 2\n"))

    def test_a_bracket_closing_the_wrong_opener_is_caught(self):
        found = self.unread("const x = [1, 2)\n")
        self.assertIsNotNone(found)
        self.assertIn("closes the", found)

    def test_an_unterminated_block_comment_is_caught(self):
        self.assertIsNotNone(self.unread("/* opened and never closed\nconst x = 1\n"))

    def test_division_is_not_read_as_a_regex(self):
        """The distinction the withdrawal claimed could not be made."""
        self.assertIsNone(self.unread("const half = total / 2\nconst q = (a + b) / c\n"))

    def test_a_regex_holding_its_own_delimiter_is_read(self):
        self.assertIsNone(self.unread('const s = t.replace(/[/"]/g, "-")\n'))

    def test_a_template_literal_may_span_lines(self):
        self.assertIsNone(self.unread("const t = `line one\nline two`\n"))

    def test_a_grammar_error_with_well_formed_tokens_passes_as_declared(self):
        """The limit, asserted so it is not later mistaken for coverage."""
        self.assertIsNone(self.unread("const x = 1 2 3\n"))


class TheGrammarReadingClosesTheLexersGap(unittest.TestCase):
    """What an engine sees that a lexer cannot, and what its absence must not look like."""

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        if sov_workflows.grammar(write(self.root, "probe.js", "const x = 1\n")) \
                is sov_workflows.NODE_UNAVAILABLE:
            self.skipTest("no JavaScript engine on this host")

    def test_a_grammar_error_with_well_formed_tokens_is_caught(self):
        """The lexer declares it cannot see this; the engine can."""
        path = write(self.root, "a.js", "export const meta = {}\nconst x = 1 2 3\n")
        self.assertIsNone(unreadable(path.read_text(encoding="utf-8")),
                          "vacuous unless the lexer really passes this")
        self.assertTrue(any("rejects it" in d for d in sov_workflows.grade(path)))

    def test_the_module_mode_is_what_reads_these_files(self):
        """`node --check` on a .js returns zero on this, because it opens with `export`.
        That is what was hand-run while two shipped workflows were unparseable."""
        source = "export const meta = {}\nconst p = 'a workflow's envelope'\n"
        path = write(self.root, "b.js", source)
        self.assertIsNotNone(sov_workflows.grammar(path))

    def test_a_top_level_return_is_not_a_defect(self):
        """This harness's runtime wraps a workflow body, so `return` at the top is legal
        there. Reporting it would refuse all twenty-three shipped files."""
        path = write(self.root, "c.js", "export const meta = {}\nreturn { ok: true }\n")
        self.assertEqual(sov_workflows.grade(path), [])

    def test_an_absent_engine_is_reported_and_never_read_as_clean(self):
        """A skipped check that satisfies its own requirement is trap T5."""
        with mock.patch.object(sov_workflows.shutil, "which", return_value=None):
            path = write(self.root, "d.js", "const x = 1\n")
            self.assertIs(sov_workflows.grammar(path), sov_workflows.NODE_UNAVAILABLE)
            self.assertEqual(sov_workflows.grade(path), [],
                             "an unread grammar must not become a defect either")


if __name__ == "__main__":
    unittest.main()
