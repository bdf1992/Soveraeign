"""Prove the checked-in node registry against its contract and the seats it names.

``scripts/sov_node.py`` reads two checked-in files and reports what they say. This
module proves the reading: that the registry validates record by record, that it agrees
with the seat topology, and that each defect the reader claims to catch is shown to be
caught rather than declared.

One case here crosses a layer on purpose. The Console Service stamps every channel and
thread with the node it serves, defaulting to a node identifier its CLI holds. If that
default and the registry's holder drift apart, the console writes records for a node the
registry has never heard of, and nothing else in the repository would notice.

Passing establishes ``BUILT`` for the reader and the registry. No peer is contacted and
no crossing is carried; the peer list is empty and the tests say so.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
# The console package imports the Record Service at module load; the cross-layer case
# below reaches a constant in its CLI, so the journal it writes through must be
# importable even though nothing here writes a record.
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from sovkernel.jsonschema import validate  # noqa: E402
from sovkernel.node_identity import registry_defects  # noqa: E402
import sov_node  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
NODE_SCHEMA = json.loads((CONTRACTS / "node-identity.schema.json").read_text("utf-8"))
REGISTRY = json.loads((FIXTURES / "node-registry.reference.json").read_text("utf-8"))
TOPOLOGY = json.loads((FIXTURES / "seat-topology.reference.json").read_text("utf-8"))


class CheckedInRegistry(unittest.TestCase):
    def test_every_record_validates_against_the_node_contract(self) -> None:
        self.assertTrue(REGISTRY["nodes"])
        for node in REGISTRY["nodes"]:
            with self.subTest(node=node["node_id"]):
                self.assertEqual(validate(node, NODE_SCHEMA), [])

    def test_the_registry_agrees_with_the_seat_topology(self) -> None:
        self.assertEqual(registry_defects(REGISTRY["nodes"], TOPOLOGY), [])

    def test_the_declared_holder_is_the_record_that_holds_it(self) -> None:
        holder = [node for node in REGISTRY["nodes"] if node["relation"] == "SELF"]
        self.assertEqual(len(holder), 1)
        self.assertEqual(REGISTRY["self_node"], holder[0]["node_id"])

    def test_no_peer_is_admitted_and_the_registry_says_so(self) -> None:
        """The accurate state of federation today, asserted rather than assumed."""
        peers = [node for node in REGISTRY["nodes"] if node["relation"] == "PEER"]
        self.assertEqual(peers, [])

    def test_the_console_default_node_is_the_node_the_registry_holds(self) -> None:
        """A console writing for a node the registry never heard of would go unnoticed."""
        from soveraeign_console_service.cli import DEFAULT_NODE

        self.assertEqual(DEFAULT_NODE, REGISTRY["self_node"])


class ReaderRefusals(unittest.TestCase):
    """Each defect the reader claims to catch, shown catching it."""

    def test_the_checked_in_registry_declares_its_own_holder(self) -> None:
        self.assertEqual(sov_node.holder_defects(REGISTRY), [])

    def test_a_registry_whose_declared_holder_disagrees_is_reported(self) -> None:
        drifted = dict(REGISTRY, self_node="node:somewhere-else")
        self.assertTrue(any("node:somewhere-else" in line
                            for line in sov_node.holder_defects(drifted)))

    def test_a_registry_with_two_holders_is_reported(self) -> None:
        holder = next(node for node in REGISTRY["nodes"] if node["relation"] == "SELF")
        second = dict(holder, node_id="node:also-local")
        doubled = dict(REGISTRY, nodes=REGISTRY["nodes"] + [second])
        self.assertTrue(any("2 holders" in line
                            for line in sov_node.holder_defects(doubled)))

    def test_a_registry_with_no_holder_is_reported(self) -> None:
        empty = dict(REGISTRY, nodes=[])
        self.assertTrue(any("no node" in line for line in sov_node.holder_defects(empty)))

    def test_a_peer_rooted_in_the_local_topology_is_reported(self) -> None:
        intruder = {
            "node_schema": "soveraeign-node-identity/v1",
            "node_id": "node:intruder",
            "display_name": "A peer holding one of our seats",
            "relation": "PEER",
            "root_seat": TOPOLOGY["root_seat"],
            "founded_at": "2026-08-20T00:00:00Z",
            "known_since": "2026-08-23T12:00:00Z",
            "admitted_by": "seat:root",
            "standing": "RECORDED",
        }
        self.assertEqual(validate(intruder, NODE_SCHEMA), [])
        defects = registry_defects(REGISTRY["nodes"] + [intruder], TOPOLOGY)
        self.assertTrue(any("node:intruder" in line for line in defects), defects)

    def test_validate_passes_on_the_checked_in_registry(self) -> None:
        self.assertEqual(sov_node.main(["validate"]), 0)

    def test_status_and_peers_read_without_reaching_anything(self) -> None:
        self.assertEqual(sov_node.main(["status"]), 0)
        self.assertEqual(sov_node.main(["peers"]), 0)


if __name__ == "__main__":
    unittest.main()
