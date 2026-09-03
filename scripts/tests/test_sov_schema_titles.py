"""Prove the schema-title check both admits a clean title and refuses a stale one.

Every case has a defeating counterpart (`AGENTS.md`, Testing and verification). A
checker that only ever sees the checked-in tree proves nothing about what it
would catch, so the defeating cases here build a throwaway contracts/decisions
pair under a TemporaryDirectory rather than mutating anything checked in.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_schema_titles  # noqa: E402

STANDING = json.loads((ROOT / "contracts" / "decision-standing.json").read_text("utf-8"))

DECISION_BODY = (
    "# 0061 - Concerns keep their source; execution artifacts do not\n\n"
    "Status: `OWNER-DIRECTED`\n\n## Decision\n\nBody text.\n"
)


class _FixtureTree(unittest.TestCase):
    """A contracts/ + decisions/ pair this test controls end to end."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.contracts = self.root / "contracts"
        self.decisions = self.root / "decisions"
        self.contracts.mkdir()
        self.decisions.mkdir()
        (self.decisions / "0061-concern-source-and-settlement.md").write_text(
            DECISION_BODY, encoding="utf-8")
        self.standing_path = self.contracts / "decision-standing.json"
        self.standing_path.write_text(json.dumps(STANDING), encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_schema(self, name: str, title: str) -> None:
        (self.contracts / name).write_text(
            json.dumps({"title": title, "type": "object"}), encoding="utf-8")

    def _check(self) -> int:
        return sov_schema_titles.check_tree(
            contracts_dir=self.contracts, decisions_dir=self.decisions,
            standing_path=self.standing_path)


class CheckedInState(unittest.TestCase):
    """The repository as it stands passes its own gate."""

    def test_the_checked_in_titles_have_no_defect(self) -> None:
        self.assertEqual(sov_schema_titles.check(), 0)

    def test_no_checked_in_title_carries_a_standing_word(self) -> None:
        standing = STANDING
        forbidden = sov_schema_titles.forbidden_standing_words(standing)
        for entry in sov_schema_titles.schema_titles():
            defects = sov_schema_titles.title_defects(entry, standing, forbidden)
            self.assertEqual(defects, [], entry["title"])

    def test_every_cited_decision_resolves_to_a_known_standing(self) -> None:
        for row in sov_schema_titles.graded():
            for citation in row["citations"]:
                self.assertIsNotNone(citation["status_line"], row["name"])
                self.assertIsNotNone(citation["standing"], row["name"])


class PositiveCase(_FixtureTree):
    """A title that cites its decision and asserts nothing about its standing passes."""

    def test_a_bare_citation_with_no_standing_word_passes(self) -> None:
        self._write_schema("thing.schema.json", "Soveraeign Thing (decisions/0061)")
        self.assertEqual(self._check(), 0)

    def test_a_title_with_no_citation_and_no_standing_word_passes(self) -> None:
        self._write_schema("thing.schema.json", "Soveraeign Thing")
        self.assertEqual(self._check(), 0)


class DefeatingCase(_FixtureTree):
    """The exact drift this check exists to catch: a title claiming a standing."""

    def test_a_title_that_still_says_proposed_fails(self) -> None:
        """decisions/0061 is OWNER-DIRECTED; a title still claiming PROPOSED is stale."""
        self._write_schema("thing.schema.json", "Soveraeign Thing (PROPOSED, decisions/0061)")
        self.assertEqual(self._check(), 1)

    def test_a_standing_word_with_no_citation_at_all_still_fails(self) -> None:
        self._write_schema("thing.schema.json", "Soveraeign Thing (PROPOSED)")
        self.assertEqual(self._check(), 1)

    def test_a_citation_to_a_decision_that_does_not_exist_fails(self) -> None:
        self._write_schema("thing.schema.json", "Soveraeign Thing (decisions/9999)")
        self.assertEqual(self._check(), 1)

    def test_a_hyphenated_standing_spelling_is_still_caught(self) -> None:
        self._write_schema("thing.schema.json", "Soveraeign Thing (OWNER-DIRECTED, decisions/0061)")
        self.assertEqual(self._check(), 1)

    def test_a_standing_word_as_a_substring_of_ordinary_prose_is_not_a_false_positive(self) -> None:
        """PROPOSED must be a whole token; a word merely containing it must not fire."""
        self._write_schema("thing.schema.json", "Soveraeign UNPROPOSED-ish Thing")
        self.assertEqual(self._check(), 0)


if __name__ == "__main__":
    unittest.main()
