"""Prove the diagram grader reads provenance rather than trusting it.

``scripts/sov_diagrams.py selfcheck`` grades six declared cases against a scratch
view. This module proves what that corpus cannot: that the grader parses the real
header shape including wrapped continuation lines, that ``stamp`` changes only the
digest field, and that every checked-in view is currently readable.

Passing establishes ``BUILT`` for the grader. It witnesses nothing, and it says
nothing at all about whether any diagram's drawing is correct - only whether the
view still reads the bytes it claims to have read.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_diagrams  # noqa: E402


WRAPPED = """# Wrapped

```text
source          CONTRACT.md · SPEC.md ·
                CLASSIFICATION.md
source_digest   {a} · {b} ·
                {c}
reader          hand-authored · v1
fidelity        LOSSY
omissions       everything, which is what a diagram is for;
                a second omission line that must not be read as a field
```

body
"""


def live(name: str) -> str:
    return sha256((ROOT / name).read_bytes()).hexdigest()[:16]


def wrapped_view() -> str:
    return WRAPPED.format(a=live("CONTRACT.md"), b=live("SPEC.md"),
                          c=live("CLASSIFICATION.md"))


class HeaderParsing(unittest.TestCase):
    """The header is fixed-width text, and a wrapped value is one value."""

    def test_a_wrapped_source_list_is_rejoined_not_truncated(self):
        header = sov_diagrams.provenance(wrapped_view())
        pairs = sov_diagrams.readings(header)
        self.assertEqual([source for source, _ in pairs],
                         ["CONTRACT.md", "SPEC.md", "CLASSIFICATION.md"])

    def test_a_wrapped_omissions_line_is_not_read_as_a_field(self):
        header = sov_diagrams.provenance(wrapped_view())
        self.assertIn("second omission line", header["omissions"])
        self.assertNotIn("a second omission line", header["source"])

    def test_a_view_with_no_provenance_block_refuses_rather_than_passing(self):
        with self.assertRaises(sov_diagrams.ProvenanceError):
            sov_diagrams.provenance("# no block here\n\nbody\n")

    def test_a_count_mismatch_refuses_rather_than_zipping_short(self):
        header = {"source": "CONTRACT.md · SPEC.md", "source_digest": "abcd"}
        with self.assertRaises(sov_diagrams.ProvenanceError):
            sov_diagrams.readings(header)


class Grading(unittest.TestCase):
    """A verdict is derived from the bytes, never from what the view asserts."""

    def setUp(self):
        self.scratch = ROOT / "diagrams" / ".test-scratch.md"
        self.addCleanup(self.scratch.unlink, True)

    def test_a_view_whose_sources_are_unchanged_reads_current(self):
        self.scratch.write_text(wrapped_view(), encoding="utf-8")
        self.assertEqual(sov_diagrams.grade(self.scratch)["verdict"], "CURRENT")

    def test_one_moved_source_among_three_is_enough_to_read_stale(self):
        self.scratch.write_text(
            wrapped_view().replace(live("SPEC.md"), "0" * 16), encoding="utf-8")
        result = sov_diagrams.grade(self.scratch)
        self.assertEqual(result["verdict"], "STALE")
        self.assertEqual(len(result["defects"]), 1)
        self.assertIn("SPEC.md", result["defects"][0])

    def test_a_declared_source_that_does_not_exist_is_invalid_not_stale(self):
        self.scratch.write_text(
            wrapped_view().replace("CONTRACT.md", "NOT-A-FILE.md", 1), encoding="utf-8")
        self.assertEqual(sov_diagrams.grade(self.scratch)["verdict"], "INVALID")


class Stamping(unittest.TestCase):
    """Stamping records a re-reading of the sources and touches nothing else."""

    def setUp(self):
        self.scratch = ROOT / "diagrams" / ".test-scratch.md"
        self.addCleanup(self.scratch.unlink, True)

    def test_stamping_a_stale_view_makes_it_current(self):
        self.scratch.write_text(
            wrapped_view().replace(live("SPEC.md"), "0" * 16), encoding="utf-8")
        self.assertEqual(len(sov_diagrams.stamp(self.scratch)), 1)
        self.assertEqual(sov_diagrams.grade(self.scratch)["verdict"], "CURRENT")

    def test_stamping_reports_nothing_and_changes_nothing_when_already_current(self):
        self.scratch.write_text(wrapped_view(), encoding="utf-8")
        before = self.scratch.read_text(encoding="utf-8")
        self.assertEqual(sov_diagrams.stamp(self.scratch), [])
        self.assertEqual(self.scratch.read_text(encoding="utf-8"), before)

    def test_stamping_leaves_every_other_field_and_the_body_intact(self):
        self.scratch.write_text(
            wrapped_view().replace(live("SPEC.md"), "0" * 16), encoding="utf-8")
        sov_diagrams.stamp(self.scratch)
        header = sov_diagrams.provenance(self.scratch.read_text(encoding="utf-8"))
        self.assertEqual(header["reader"], "hand-authored · v1")
        self.assertEqual(header["fidelity"], "LOSSY")
        self.assertIn("second omission line", header["omissions"])
        self.assertIn("body", self.scratch.read_text(encoding="utf-8"))


class EveryCheckedInView(unittest.TestCase):
    """The corpus itself has to stay gradeable, not merely current."""

    def test_there_are_views_to_grade(self):
        self.assertGreater(len(sov_diagrams.views()), 0)

    def test_no_view_is_ungradeable(self):
        invalid = [item["view"] for item in map(sov_diagrams.grade, sov_diagrams.views())
                   if item["verdict"] == "INVALID"]
        self.assertEqual(invalid, [])

    def test_the_readme_is_not_graded_as_a_view(self):
        self.assertNotIn("README.md", [path.name for path in sov_diagrams.views()])


if __name__ == "__main__":
    unittest.main()
