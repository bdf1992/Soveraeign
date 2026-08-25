"""Execute the direction half of the federation-crossing fixtures (decisions/0039).

``scripts/tests/test_contract_fixtures.py`` proves each entry's ``record`` against
``contracts/federation-crossing.schema.json``. This module proves what a single record
cannot state: which side of the crossing the reading node is on, whether that node may
settle the offer at all, and whose seat produced it.

The reference registry below is the one the node-identity fixtures already declare, so
the two contracts are graded against the same two nodes rather than against separate
inventions.

Passing establishes ``BUILT`` for the contract only. No crossing is carried, no peer is
contacted, and federation remains a proposal.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.federation import crossing_defects, peers  # noqa: E402
from sovkernel.node_identity import registry_defects  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
TOPOLOGY = json.loads((FIXTURES / "seat-topology.reference.json").read_text("utf-8"))
NODES = json.loads((FIXTURES / "node-identity.fixtures.json").read_text("utf-8"))
ENTRIES = json.loads((FIXTURES / "federation-crossing.fixtures.json").read_text("utf-8"))
GRADED = [entry for entry in ENTRIES if "expected_crossing" in entry]
# The two nodes the node-identity fixtures declare admissible, reused verbatim so a
# crossing is never graded against a registry that node_identity itself would reject.
REGISTRY = [entry["record"] for entry in NODES
            if entry["id"] in ("NODE-POS-SELF", "NODE-POS-PEER")]


class FederationCrossingFixtures(unittest.TestCase):
    def test_the_reference_registry_is_itself_admissible(self) -> None:
        """The two contracts compose: crossings are graded against a sound registry."""
        self.assertEqual(registry_defects(REGISTRY, TOPOLOGY), [])
        self.assertEqual(peers(REGISTRY), ["node:peer-one"])

    def test_every_graded_entry_matches_its_declared_expectation(self) -> None:
        self.assertGreaterEqual(len(GRADED), 2)
        for entry in GRADED:
            with self.subTest(case=entry["id"]):
                defects = crossing_defects([entry["record"]], REGISTRY, TOPOLOGY)
                if entry["expected_crossing"]:
                    self.assertEqual(defects, [], entry["id"])
                else:
                    self.assertNotEqual(defects, [], entry["id"])

    def test_every_schema_valid_defeating_entry_is_graded(self) -> None:
        """A defeating entry the schema accepts must be caught here or nowhere."""
        for entry in ENTRIES:
            if entry["polarity"] == "defeating" and entry["expected_validity"] == "VALID":
                with self.subTest(case=entry["id"]):
                    self.assertIn("expected_crossing", entry)
                    self.assertFalse(entry["expected_crossing"])

    def test_direction_is_what_decides_who_may_settle(self) -> None:
        """The claim decisions/0039 rests on, stated as an executable case.

        One crossing, one settlement, read twice. Addressed to this node it is an
        ordinary admission; sent by this node it is this node claiming to know how a
        peer ruled. Nothing changes but which side the holder is on.
        """
        settled = {
            "crossing_schema": "soveraeign-federation-crossing/v1",
            "crossing_id": "crossing:probe",
            "from_node": "node:peer-one",
            "to_node": "node:home",
            "origin_seat": "seat:peer-one-root",
            "offer": {
                "record_kind": "thread",
                "record_address": "thread/T-1",
                "record_digest": "sha256:abcd",
                "standing_at_origin": "EFFECTIVE",
            },
            "offered_at": "2026-08-23T12:00:00Z",
            "admission": {
                "admitted_by": "seat:root",
                "admitted_at": "2026-08-23T12:01:00Z",
                "outcome": "COMMITTED",
                "reason_code": None,
                "local_record_address": "thread/local-1",
                "local_standing": "RECORDED",
            },
            "standing": "RECORDED",
        }
        self.assertEqual(crossing_defects([settled], REGISTRY, TOPOLOGY), [])

        outbound = dict(settled, from_node="node:home", to_node="node:peer-one",
                        origin_seat="seat:root")
        self.assertNotEqual(crossing_defects([outbound], REGISTRY, TOPOLOGY), [])

    def test_a_registry_with_no_holder_gives_every_crossing_no_holder(self) -> None:
        peers_only = [node for node in REGISTRY if node["relation"] == "PEER"]
        defects = crossing_defects([ENTRIES[0]["record"]], peers_only, TOPOLOGY)
        self.assertEqual(len(defects), 1)
        self.assertIn("SELF", defects[0])

    def test_an_admitted_offer_never_arrives_above_recorded(self) -> None:
        """Whatever a peer says its record stands at, the local record starts at RECORDED."""
        admitted = [entry["record"] for entry in ENTRIES
                    if entry["expected_validity"] == "VALID"
                    and (entry["record"]["admission"] or {}).get("outcome") == "COMMITTED"]
        self.assertTrue(admitted)
        for record in admitted:
            with self.subTest(crossing=record["crossing_id"]):
                self.assertEqual(record["admission"]["local_standing"], "RECORDED")


if __name__ == "__main__":
    unittest.main()
