"""Execute the registry half of the node-identity fixtures (decisions/0039).

``scripts/tests/test_contract_fixtures.py`` already proves each entry's ``record``
against ``contracts/node-identity.schema.json``. This module proves the half a schema
cannot express, because every rule here is a property of the registry read against the
seat topology it belongs to rather than of any single record.

An entry may carry ``context``, the node records already in the registry, so a defect
that only exists between two records has somewhere to live. The guard runs over
``context + [record]``.

Passing establishes ``BUILT`` for the contract only. Federation is a proposal, no
crossing is admitted, and nothing here contacts another node.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402
from sovkernel.node_identity import registry_defects  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
SEAT_SCHEMA = json.loads((CONTRACTS / "seat-registry.schema.json").read_text("utf-8"))
NODE_SCHEMA = json.loads((CONTRACTS / "node-identity.schema.json").read_text("utf-8"))
TOPOLOGY = json.loads((FIXTURES / "seat-topology.reference.json").read_text("utf-8"))
ENTRIES = json.loads((FIXTURES / "node-identity.fixtures.json").read_text("utf-8"))
GRADED = [entry for entry in ENTRIES if "expected_registry" in entry]


def _registry(entry: dict) -> list[dict]:
    return list(entry.get("context", [])) + [entry["record"]]


class NodeIdentityFixtures(unittest.TestCase):
    def test_the_reference_topology_is_a_valid_seat_registry(self) -> None:
        """The two contracts compose: node identity is graded against a real seat projection."""
        self.assertEqual(validate(TOPOLOGY, SEAT_SCHEMA), [])

    def test_every_graded_entry_matches_its_declared_registry_expectation(self) -> None:
        self.assertGreaterEqual(len(GRADED), 2)
        for entry in GRADED:
            with self.subTest(case=entry["id"]):
                defects = registry_defects(_registry(entry), TOPOLOGY)
                if entry["expected_registry"]:
                    self.assertEqual(defects, [], entry["id"])
                else:
                    self.assertNotEqual(defects, [], entry["id"])

    def test_every_schema_valid_defeating_entry_is_graded(self) -> None:
        """A defeating entry the schema accepts must be caught here or nowhere."""
        for entry in ENTRIES:
            if entry["polarity"] == "defeating" and entry["expected_validity"] == "VALID":
                with self.subTest(case=entry["id"]):
                    self.assertIn("expected_registry", entry)
                    self.assertFalse(entry["expected_registry"])

    def test_every_context_record_is_itself_a_valid_node_identity(self) -> None:
        """A defect must come from the graded record, not from malformed context."""
        for entry in ENTRIES:
            for index, record in enumerate(entry.get("context", [])):
                with self.subTest(case=entry["id"], context=index):
                    self.assertEqual(validate(record, NODE_SCHEMA), [])

    def test_a_peer_root_seat_absent_from_the_topology_is_what_makes_it_a_peer(self) -> None:
        """The claim decisions/0039 rests on, stated as an executable case.

        Moving one peer's root seat into the local topology must be the difference
        between an admissible registry and a defective one, with nothing else changed.
        """
        peer = {
            "node_schema": "soveraeign-node-identity/v1",
            "node_id": "node:probe",
            "display_name": "A probe peer",
            "relation": "PEER",
            "root_seat": "seat:probe-root",
            "founded_at": "2026-08-20T00:00:00Z",
            "known_since": "2026-08-23T12:00:00Z",
            "admitted_by": "seat:root",
            "standing": "RECORDED",
        }
        holder = {
            "node_schema": "soveraeign-node-identity/v1",
            "node_id": "node:home",
            "display_name": "Bdo's node",
            "relation": "SELF",
            "root_seat": "seat:root",
            "founded_at": "2026-08-22T00:00:00Z",
            "known_since": None,
            "admitted_by": None,
            "standing": "RECORDED",
        }
        self.assertEqual(validate(peer, NODE_SCHEMA), [])
        self.assertEqual(registry_defects([holder, peer], TOPOLOGY), [])

        local_root = dict(peer, root_seat=TOPOLOGY["root_seat"])
        self.assertEqual(validate(local_root, NODE_SCHEMA), [])
        self.assertNotEqual(registry_defects([holder, local_root], TOPOLOGY), [])

    def test_a_registry_with_no_holder_is_defective(self) -> None:
        """A registry of peers alone answers no question about whose registry it is."""
        peers = [entry["record"] for entry in ENTRIES
                 if entry["record"]["relation"] == "PEER"][:1]
        self.assertTrue(peers)
        self.assertNotEqual(registry_defects(peers, TOPOLOGY), [])


if __name__ == "__main__":
    unittest.main()
