"""Every refusal `contracts/lessons-loop.json` declares, fired by a case.

The cases build small pages rather than editing the real one, so a lesson being
written, drained, or renumbered never breaks these. The two tests that do read
`LESSONS.md` assert the relation the contract states and not the counts, for the
same reason.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import sov_lessons as lessons  # noqa: E402


def contract() -> dict:
    return json.loads((ROOT / lessons.CONTRACT).read_bytes().decode("utf-8"))


def codes(defects: list[dict]) -> set[str]:
    return {defect["code"] for defect in defects}


def page(*blocks: str, recorded: int | None = None, threshold: int = 7) -> str:
    """A minimal lessons page holding the given entry blocks."""
    if recorded is None:
        recorded = sum(1 for block in blocks if "`RECORDED`" in block)
    return (
        "# Lessons\n\n"
        f"Standing now: **{recorded} `RECORDED`**, threshold {threshold}.\n\n"
        "## Entries\n\n" + "\n".join(blocks) + "\n## Dropped\n\nNone yet.\n"
    )


def entry(identifier: str = "L-0001", standing: str = "RECORDED",
          landing: str = "fixture", body: str = "") -> str:
    return (f"### {identifier} · A title\n\nSomething happened.\n{body}\n"
            f"- Landing: `{landing}` - a sentence.\n"
            f"- Standing: `{standing}`.\n\n")


class TheLivePage(unittest.TestCase):
    """What LESSONS.md reads today, stated as a relation rather than a count."""

    def test_the_page_grades_clean(self):
        text = (ROOT / lessons.PAGE).read_bytes().decode("utf-8")
        self.assertEqual([], lessons.grade(text, contract()))

    def test_every_entry_is_numbered_and_distinct(self):
        text = (ROOT / lessons.PAGE).read_bytes().decode("utf-8")
        found = [record["id"] for record in lessons.entries(text)]
        self.assertTrue(all(found))
        self.assertEqual(len(found), len(set(found)))


class FalseEffective(unittest.TestCase):
    """EFFECTIVE means it runs in verify or lint; the page may not assert otherwise."""

    def test_effective_naming_no_reached_path_refuses(self):
        text = page(entry(standing="EFFECTIVE", landing="lint",
                          body="- Evidence: `scripts/not_a_check.py` does the work."))
        self.assertIn("FALSE_EFFECTIVE", codes(lessons.grade(text, contract())))

    def test_effective_naming_a_check_table_path_passes(self):
        reached = lessons.reachable_paths()
        self.assertIn("scripts/lint.py", reached)
        text = page(entry(standing="EFFECTIVE", landing="lint",
                          body="- Landed as `scripts/lint.py`, run every check."))
        self.assertNotIn("FALSE_EFFECTIVE", codes(lessons.grade(text, contract())))

    def test_a_recorded_entry_naming_nothing_is_not_refused(self):
        """Capture is not taxed: an entry that has landed nowhere is the normal state."""
        text = page(entry(standing="RECORDED"))
        self.assertNotIn("FALSE_EFFECTIVE", codes(lessons.grade(text, contract())))


class FalseAdmitted(unittest.TestCase):
    """ADMITTED means a fixture passes for it, so the fixture has to be there."""

    def test_admitted_with_a_fixture_landing_and_no_path_refuses(self):
        text = page(entry(standing="ADMITTED", landing="fixture",
                          body="- Evidence: `conformance/fixtures/absent.json`."))
        self.assertIn("FALSE_ADMITTED", codes(lessons.grade(text, contract())))

    def test_admitted_with_a_present_path_passes(self):
        text = page(entry(standing="ADMITTED", landing="fixture",
                          body="- Evidence: `contracts/lessons-loop.json`."))
        self.assertNotIn("FALSE_ADMITTED", codes(lessons.grade(text, contract())))

    def test_a_decision_landing_is_not_graded_for_a_path(self):
        """A judgement landing has no fixture to point at and is not asked for one."""
        text = page(entry(standing="RATIFIED", landing="decision"))
        self.assertNotIn("FALSE_ADMITTED", codes(lessons.grade(text, contract())))


class VocabularyIsClosed(unittest.TestCase):
    """A synonym for a standing is a second vocabulary, which AGENTS.md refuses."""

    def test_an_unknown_standing_refuses(self):
        text = page(entry(standing="PENDING"))
        self.assertIn("UNKNOWN_STANDING", codes(lessons.grade(text, contract())))

    def test_a_missing_standing_refuses(self):
        text = page("### L-0001 · A title\n\n- Landing: `fixture` - a sentence.\n\n",
                    recorded=0)
        self.assertIn("UNKNOWN_STANDING", codes(lessons.grade(text, contract())))

    def test_an_unknown_landing_refuses(self):
        text = page(entry(landing="someday"))
        self.assertIn("UNKNOWN_LANDING", codes(lessons.grade(text, contract())))

    def test_a_missing_landing_refuses(self):
        text = page("### L-0001 · A title\n\n- Standing: `RECORDED`.\n\n")
        self.assertIn("UNDECLARED_LANDING", codes(lessons.grade(text, contract())))


class Identifiers(unittest.TestCase):
    """A lesson is cited by identifier, so a duplicate makes a citation ambiguous."""

    def test_an_unnumbered_entry_refuses(self):
        text = page("### A title with no number\n\n- Landing: `fixture` - x.\n"
                    "- Standing: `RECORDED`.\n\n")
        self.assertIn("UNNUMBERED_ENTRY", codes(lessons.grade(text, contract())))

    def test_a_duplicate_identifier_refuses(self):
        text = page(entry("L-0009"), entry("L-0009"))
        self.assertIn("UNNUMBERED_ENTRY", codes(lessons.grade(text, contract())))


class TheHeaderIsGraded(unittest.TestCase):
    """The page summarises itself and every reader reads the summary, not the entries."""

    def test_a_summary_disagreeing_with_the_entries_refuses(self):
        text = page(entry("L-0001"), entry("L-0002"), recorded=5)
        self.assertIn("HEADER_DISAGREES", codes(lessons.grade(text, contract())))

    def test_a_summary_naming_another_threshold_refuses(self):
        text = page(entry(), threshold=99)
        self.assertIn("HEADER_DISAGREES", codes(lessons.grade(text, contract())))

    def test_a_page_with_no_summary_refuses(self):
        text = "# Lessons\n\n## Entries\n\n" + entry() + "\n## Dropped\n\nNone.\n"
        self.assertIn("HEADER_DISAGREES", codes(lessons.grade(text, contract())))


class TheDrainDoesNotRefuse(unittest.TestCase):
    """decisions/0029 declined to charge for capture, and this does not reverse it."""

    def test_the_contract_declares_the_drain_non_refusing(self):
        self.assertFalse(contract()["drain"]["refuses"])

    def test_a_page_past_its_threshold_adds_no_defect(self):
        blocks = [entry(f"L-{index:04d}") for index in range(1, 12)]
        self.assertEqual([], lessons.grade(page(*blocks), contract()))

    def test_a_page_past_its_threshold_reads_as_due(self):
        blocks = [entry(f"L-{index:04d}") for index in range(1, 12)]
        state = lessons.drain(page(*blocks), contract())
        self.assertTrue(state["due"])
        self.assertEqual(11, state["recorded"])


class DroppedEntriesAreNotGraded(unittest.TestCase):
    """A dropped entry keeps its reason on the page and is no longer a live claim."""

    def test_the_dropped_section_is_excluded(self):
        text = (page(entry("L-0001"))
                + "### L-0002 · dropped with no landing\n\nno fields here\n")
        self.assertEqual([], lessons.grade(text, contract()))


class EveryDeclaredRefusalFires(unittest.TestCase):
    """The contract may not declare a refusal no case in this file reaches."""

    def test_the_declared_refusals_are_exactly_the_reachable_ones(self):
        declared = {refusal["code"] for refusal in contract()["refusals"]}
        reached = {"FALSE_EFFECTIVE", "FALSE_ADMITTED", "UNDECLARED_LANDING",
                   "UNKNOWN_STANDING", "UNKNOWN_LANDING", "HEADER_DISAGREES",
                   "UNNUMBERED_ENTRY"}
        self.assertEqual(declared, reached)


class TheContractMatchesItsRecord(unittest.TestCase):
    """decisions/0029 owns the loop; this contract may not quietly restate it wrong."""

    def test_the_four_standings_are_the_ones_the_record_names(self):
        self.assertEqual({"RECORDED", "ADMITTED", "RATIFIED", "EFFECTIVE"},
                         set(contract()["standings"]))

    def test_the_threshold_is_the_one_the_record_set(self):
        record = (ROOT / "decisions/0029-lessons-loop.md").read_bytes().decode("utf-8")
        self.assertIn("threshold at seven", record)
        self.assertEqual(7, contract()["drain"]["threshold"])


if __name__ == "__main__":
    unittest.main()
