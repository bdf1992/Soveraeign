"""Positive and defeating cases for how documents are classified.

The claim under test: every facet is derived from a record this repository
already carries, and nothing silently lands in a default bucket. These defeat it
by asking for a document no rule claims, a standing phrasing no grade knows, and
a taxonomy that has drifted from the corpus it describes.

BUILT evidence only.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_docs  # noqa: E402
from sovdocs import facets  # noqa: E402


BOUNDARY_ROW = re.compile(r"^\|\s*`/([a-z]+)(?:/<[a-z]+>)?`\s*\|", re.M)


def _agents_boundaries() -> set[str]:
    """The directory names the AGENTS.md boundary table declares."""
    table = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    after = table.split("## Directory boundaries", 1)[-1]
    section = after.split(chr(10) + "## ", 1)[0]
    return set(BOUNDARY_ROW.findall(section))


class Kind(unittest.TestCase):
    def test_every_published_document_is_claimed_by_a_rule(self):
        for source in sov_docs.sources():
            path = source.relative_to(ROOT).as_posix()
            self.assertTrue(facets.kind(path), path)

    def test_a_document_no_rule_claims_is_refused_not_bucketed(self):
        """The defeating case: no catch-all, so a new shape has to be decided on."""
        with self.assertRaises(facets.Unclassified) as raised:
            facets.kind("somewhere/new-shape.md")
        self.assertIn("somewhere/new-shape.md", str(raised.exception))

    def test_the_specific_rule_wins_over_the_general_one(self):
        self.assertEqual(facets.kind("services/asset/CHARTER.md"), "charter")
        self.assertEqual(facets.kind("services/asset/README.md"), "readme")
        self.assertEqual(
            facets.kind("services/asset/conformance/PROD-I-2-BUILD.md"), "report")
        self.assertEqual(facets.kind("decisions/0001-founding-boundary.md"), "decision")
        self.assertEqual(facets.kind("AGENTS.md"), "governing")

    def test_a_decision_needs_its_number_to_read_as_a_decision(self):
        """A file dropped in decisions/ without the naming shape is not a decision."""
        with self.assertRaises(facets.Unclassified):
            facets.kind("decisions/notes.md")

    def test_every_kind_carries_a_gloss(self):
        for _, name, note in facets.KIND_RULES:
            self.assertTrue(note.strip(), name)
            self.assertEqual(facets.kind_note(name), facets.kind_note(name))

    def test_drafts_are_excluded_rather_than_left_unclassified(self):
        self.assertTrue(facets.excluded(".claude/drafts/o2-ratification-packet.md"))
        self.assertFalse(facets.excluded("decisions/0001-founding-boundary.md"))

    def test_an_excluded_document_never_reaches_the_corpus(self):
        paths = {source.relative_to(ROOT).as_posix() for source in sov_docs.sources()}
        self.assertFalse([path for path in paths if facets.excluded(path)])


class Standing(unittest.TestCase):
    def setUp(self):
        self.declared = facets.service_standings(ROOT)

    def test_a_documents_own_status_line_wins(self):
        text = "# Title\n\nStatus: `PROPOSED FOR BDO RATIFICATION`\n\nBody.\n"
        self.assertEqual(facets.standing("services/asset/CHARTER.md", text, self.declared),
                         "PROPOSED FOR BDO RATIFICATION")

    def test_a_silent_service_document_falls_back_to_its_manifest(self):
        self.assertEqual(facets.standing("services/asset/README.md", "# R\n", self.declared),
                         self.declared["asset"])

    def test_a_silent_document_outside_a_service_says_it_is_unstated(self):
        """The defeating case: never guess a standing nobody wrote down."""
        self.assertEqual(facets.standing("diagrams/service-map.md", "# D\n", self.declared),
                         facets.UNSTATED)

    def test_the_decisive_token_wins_over_the_incidental_one(self):
        self.assertEqual(facets.settled("OWNER-DIRECTED - FREEZE CANDIDATE"), "proposed")
        self.assertEqual(facets.settled("OWNER-DIRECTED - RULED AT CONTROL RESOLUTION"),
                         "accepted")
        self.assertEqual(facets.settled("SUPERSEDED BY 0004"), "superseded")

    def test_an_ungraded_phrasing_keeps_its_own_words(self):
        """The defeating case: an unknown standing must not pool into a bucket."""
        self.assertEqual(facets.settled("ACTIVE SAFETY BOUNDARY"), "ACTIVE SAFETY BOUNDARY")
        self.assertEqual(facets.settled("SOMETHING NOBODY HAS WRITTEN YET"),
                         "SOMETHING NOBODY HAS WRITTEN YET")


class DerivedNotInvented(unittest.TestCase):
    """Office and village come from the tables that already assign them."""

    def setUp(self):
        self.offices = facets.Offices(ROOT)

    def test_a_service_document_inherits_its_services_office(self):
        self.assertIn(self.offices.office("services/asset/CHARTER.md"), ("FRONT", "BACK"))

    def test_a_document_outside_a_service_claims_no_office(self):
        self.assertIsNone(self.offices.office("AGENTS.md"))
        self.assertIsNone(self.offices.village_of("AGENTS.md"))

    def test_boundaries_match_the_directories_agents_md_names(self):
        """The projection drifts the moment AGENTS.md adds or drops a boundary.

        Compared as sets of names, so a failure prints the difference rather than
        the governing document (`AGENTS.md`, Context hygiene).
        """
        declared = _agents_boundaries()
        projected = {name for _, name in facets.BOUNDARIES}
        self.assertTrue(declared, "the AGENTS.md directory table could not be read")
        self.assertEqual(projected - declared, set(),
                         "projected boundaries AGENTS.md does not declare")
        self.assertEqual(declared - projected, set(),
                         "AGENTS.md declares boundaries the projection is missing")


class Grouping(unittest.TestCase):
    def setUp(self):
        self.built = sov_docs.documents({})

    def test_grouping_places_every_document_and_invents_no_bucket(self):
        groups = sov_docs.grouped(self.built)
        placed = sum(len(items) for _, items in groups)
        self.assertEqual(placed, len(self.built))
        self.assertNotIn("Elsewhere", [name for name, _ in groups])

    def test_group_order_follows_the_rule_order(self):
        declared = [name for _, name, _ in facets.KIND_RULES]
        seen = [name for name, _ in sov_docs.grouped(self.built)]
        self.assertEqual(seen, [name for name in dict.fromkeys(declared) if name in seen])

    def test_every_document_carries_its_facets(self):
        for document in self.built:
            for key in ("kind", "boundary", "standing", "settled"):
                self.assertTrue(document["facets"][key], document["path"])

    def test_the_page_offers_a_filter_for_a_facet_the_corpus_actually_has(self):
        page = sov_docs.build()
        self.assertIn('data-facet="settled"', page)
        self.assertIn('data-facet="boundary"', page)
        for document in self.built[:5]:
            self.assertIn(f'data-settled="{document["facets"]["settled"]}"', page)


if __name__ == "__main__":
    unittest.main()
