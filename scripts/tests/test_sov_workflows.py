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
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_workflows  # noqa: E402

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
        """`.replace(/"/g, "'")` in the loop defeated three earlier readings. The two that
        shipped read bytes, so it must not defeat them."""
        loop = ROOT / ".claude" / "workflows" / "sov-loop.js"
        self.assertIn('replace(/"/g', loop.read_text(encoding="utf-8"),
                      "this case is vacuous without the construction it guards against")
        self.assertEqual(sov_workflows.grade(loop), [])


if __name__ == "__main__":
    unittest.main()
