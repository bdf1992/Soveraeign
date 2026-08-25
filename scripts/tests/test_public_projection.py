"""Execute the derivation half of the public-projection fixtures (decisions/0039).

``scripts/tests/test_contract_fixtures.py`` proves each entry's ``record`` against
``contracts/public-projection.schema.json``. This module proves what the shape cannot:
that every rendered entry resolves to a declared source, that a filtered rebuild says
it filtered, that nothing appears from a node no settled crossing admitted, and that a
seat this node does not hold did not publish on its behalf.

The crossing register below is the one the federation fixtures already declare, so the
three contracts are graded against one set of nodes rather than three inventions.

Passing establishes ``BUILT`` for the contract only. Nothing here publishes, renders,
or serves anything, and the public surface remains a proposal.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.publication import projection_defects  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
TOPOLOGY = json.loads((FIXTURES / "seat-topology.reference.json").read_text("utf-8"))
CROSSINGS = json.loads((FIXTURES / "federation-crossing.fixtures.json").read_text("utf-8"))
ENTRIES = json.loads((FIXTURES / "public-projection.fixtures.json").read_text("utf-8"))
GRADED = [entry for entry in ENTRIES if "expected_projection" in entry]
# The settled inbound crossing from node:peer-one, reused verbatim. It is the single
# reason a peer's thread may appear on this node's public surface at all.
REGISTER = [entry["record"] for entry in CROSSINGS
            if entry["id"] in ("FED-POS-INBOUND-ADMITTED", "FED-POS-INBOUND-REFUSED")]


class PublicProjectionFixtures(unittest.TestCase):
    def test_every_graded_entry_matches_its_declared_expectation(self) -> None:
        self.assertGreaterEqual(len(GRADED), 2)
        for entry in GRADED:
            with self.subTest(case=entry["id"]):
                defects = projection_defects(entry["record"], REGISTER, TOPOLOGY)
                if entry["expected_projection"]:
                    self.assertEqual(defects, [], entry["id"])
                else:
                    self.assertNotEqual(defects, [], entry["id"])

    def test_every_schema_valid_defeating_entry_is_graded(self) -> None:
        """A defeating entry the schema accepts must be caught here or nowhere."""
        for entry in ENTRIES:
            if entry["polarity"] == "defeating" and entry["expected_validity"] == "VALID":
                with self.subTest(case=entry["id"]):
                    self.assertIn("expected_projection", entry)
                    self.assertFalse(entry["expected_projection"])

    def test_an_admitted_crossing_is_what_lets_a_peer_thread_be_published(self) -> None:
        """The integration point between the three contracts, as an executable case.

        One projection carrying one peer thread, read against two registers. With the
        settled inbound admission it is publishable; with only a refused one it is not.
        Nothing about the projection changes.
        """
        projection = next(entry["record"] for entry in ENTRIES
                          if entry["id"] == "PUB-POS-ADMITTED-PEER-THREAD")
        self.assertEqual(projection_defects(projection, REGISTER, TOPOLOGY), [])

        refused_only = [crossing for crossing in REGISTER
                        if crossing["admission"]["outcome"] == "REFUSED"]
        defects = projection_defects(projection, refused_only, TOPOLOGY)
        self.assertTrue(any("node:peer-one" in line for line in defects), defects)

    def test_an_outbound_crossing_admits_nothing_here(self) -> None:
        """Offering a record to a peer is not this node admitting one from it."""
        projection = next(entry["record"] for entry in ENTRIES
                          if entry["id"] == "PUB-POS-ADMITTED-PEER-THREAD")
        outbound = [crossing for crossing in
                    (entry["record"] for entry in CROSSINGS)
                    if crossing["from_node"] == "node:home"]
        self.assertTrue(outbound)
        self.assertNotEqual(projection_defects(projection, outbound, TOPOLOGY), [])

    def test_an_empty_projection_is_admissible_and_declares_no_omissions(self) -> None:
        """A node that published nothing still says so rather than leaving it undefined."""
        empty = next(entry["record"] for entry in ENTRIES
                     if entry["id"] == "PUB-POS-NOTHING-PUBLISHED")
        self.assertEqual(projection_defects(empty, REGISTER, TOPOLOGY), [])
        self.assertEqual(empty["entries"], [])
        self.assertEqual(empty["omissions"], [])

    def test_dropping_one_entry_without_declaring_it_defeats_a_sound_projection(self) -> None:
        """The silent-filter rule, shown by removing one entry from a passing view."""
        sound = next(entry["record"] for entry in ENTRIES
                     if entry["id"] == "PUB-POS-LOCAL-THREADS")
        self.assertEqual(projection_defects(sound, REGISTER, TOPOLOGY), [])
        filtered = dict(sound, entries=sound["entries"][:1], omissions=[])
        defects = projection_defects(filtered, REGISTER, TOPOLOGY)
        self.assertTrue(any("omissions" in line for line in defects), defects)


if __name__ == "__main__":
    unittest.main()
