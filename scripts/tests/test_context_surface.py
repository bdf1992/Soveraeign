"""Prove the context-surface reading measures the tree rather than describing it.

``scripts/sov_context.py`` exists because a compression pass graded on its own
account of itself is not graded. That only holds if the reader itself measures.
Each case here builds a small tree whose answer is known by construction, so a
reader that returned a plausible constant instead of a count would fail.

The defeating half is the point: every metric is shown to move when the tree
moves, and to move in the direction the metric claims. Passing establishes
``BUILT`` for the reader. It witnesses nothing and settles no standing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovcontext import surface  # noqa: E402


def _tree(root: Path, files: dict[str, str]) -> None:
    """Write a small repository-shaped tree."""
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


class ReachMeasuresTheTree(unittest.TestCase):
    """An entrypoint nothing names is found, and naming it clears the finding."""

    def test_unnamed_entrypoint_is_reported(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {
                "scripts/sov_named.py": "print(1)\n",
                "scripts/sov_hidden.py": "print(2)\n",
                "README.md": "Run python scripts/sov_named.py to start.\n",
            })
            reading = surface.reach(root)
            self.assertEqual(reading["entrypoints"], 2)
            self.assertEqual(reading["unnamed"], ["sov_hidden.py"])

    def test_naming_the_entrypoint_clears_it(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {
                "scripts/sov_hidden.py": "print(2)\n",
                "README.md": "Run python scripts/sov_hidden.py to start.\n",
            })
            self.assertEqual(surface.reach(root)["unnamed"], [])

    def test_a_named_script_that_does_not_exist_is_a_dangling_route(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {"README.md": "Run python scripts/sov_absent.py.\n"})
            self.assertIn("sov_absent.py", surface.reach(root)["dangling"])


class RedundancyCountsProducers(unittest.TestCase):
    """A fact stated once has no restatement; stating it again is counted."""

    def test_one_producer_is_not_a_restatement(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {"AGENTS.md": "Run python scripts/verify.py before landing.\n"})
            facts = {f["fact"]: f for f in surface.redundancy(root)["facts"]}
            self.assertEqual(facts["verify-command"]["producers"], 1)
            self.assertEqual(facts["verify-command"]["restatements"], 0)

    def test_a_second_producer_is_counted_as_a_restatement(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {
                "AGENTS.md": "Run python scripts/verify.py before landing.\n",
                "CONTRIBUTING.md": "Contributors run python scripts/verify.py too.\n",
            })
            facts = {f["fact"]: f for f in surface.redundancy(root)["facts"]}
            self.assertEqual(facts["verify-command"]["producers"], 2)
            self.assertEqual(facts["verify-command"]["restatements"], 1)

    def test_a_fact_no_file_states_has_no_producer(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {"README.md": "Nothing normative here.\n"})
            facts = {f["fact"]: f for f in surface.redundancy(root)["facts"]}
            self.assertEqual(facts["effect-classes"]["producers"], 0)


class RoutesCountEdgesNotMentions(unittest.TestCase):
    """Fan-out counts distinct governing targets, and never the document itself."""

    def test_distinct_targets_are_counted_once(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {
                "AGENTS.md": "See SPEC.md and SPEC.md and STATUS.yaml.\n",
                "SPEC.md": "No outbound reference.\n",
                "STATUS.yaml": "phase: test\n",
            })
            reading = surface.routes(root)
            by_doc = {r["doc"]: r for r in reading["by_document"]}
            self.assertEqual(by_doc["AGENTS.md"]["out"], 2)
            self.assertEqual(reading["edges"], 2)

    def test_a_document_naming_itself_is_not_an_edge(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {"AGENTS.md": "AGENTS.md governs the repository.\n"})
            self.assertEqual(surface.routes(root)["edges"], 0)

    def test_a_reference_to_an_absent_document_is_not_an_edge(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {"AGENTS.md": "See GONE.md for the rule.\n"})
            self.assertEqual(surface.routes(root)["edges"], 0)


class VolumeCountsLines(unittest.TestCase):
    """Orientation volume moves with the text, and separates from the total."""

    def test_orientation_excludes_surfaces_reached_only_after_a_concern(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {
                "AGENTS.md": "one\ntwo\nthree\n",
                "decisions/0001-x.md": "a\nb\nc\nd\ne\n",
            })
            reading = surface.volume(root)
            self.assertEqual(reading["orientation_lines"], 3)
            self.assertEqual(reading["total_lines"], 8)

    def test_cutting_orientation_text_lowers_the_headline(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            _tree(root, {"AGENTS.md": "one\ntwo\nthree\nfour\n"})
            before = surface.checkpoint(root)["headline"]["orientation_lines"]
            (root / "AGENTS.md").write_text("one\ntwo\n", encoding="utf-8")
            after = surface.checkpoint(root)["headline"]["orientation_lines"]
            self.assertEqual((before, after), (4, 2))


if __name__ == "__main__":
    unittest.main()
