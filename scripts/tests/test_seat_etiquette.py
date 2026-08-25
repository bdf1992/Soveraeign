"""Execute the etiquette half of the seat-message fixtures (decisions/0035).

``scripts/tests/test_contract_fixtures.py`` already proves each entry's ``record``
against ``contracts/seat-message.schema.json``; this module proves the half a schema
cannot express. Etiquette is a property of a sequence, so an entry may carry
``context``, the statements made before its record, and the guard runs over
``context + [record]``.

Passing establishes ``BUILT`` for the contract only. The etiquette itself is a
proposal, and nothing here checks live agent output.
"""

from __future__ import annotations

from pathlib import Path
import json
import unittest
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402
from sovkernel.seat_etiquette import conversation_defects  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
SEAT_SCHEMA = json.loads((CONTRACTS / "seat-registry.schema.json").read_text("utf-8"))
ETIQUETTE = json.loads((CONTRACTS / "seat-etiquette.json").read_text("utf-8"))
TOPOLOGY = json.loads((FIXTURES / "seat-topology.reference.json").read_text("utf-8"))
ENTRIES = json.loads((FIXTURES / "seat-message.fixtures.json").read_text("utf-8"))
GRADED = [entry for entry in ENTRIES if "expected_etiquette" in entry]


def _conversation(entry: dict) -> list[dict]:
    return list(entry.get("context", [])) + [entry["record"]]


class SeatEtiquetteFixtures(unittest.TestCase):
    def test_the_reference_topology_is_a_valid_seat_registry(self) -> None:
        """The two contracts compose: etiquette is graded against a real seat projection."""
        self.assertEqual(validate(TOPOLOGY, SEAT_SCHEMA), [])

    def test_every_graded_entry_matches_its_declared_etiquette_expectation(self) -> None:
        self.assertGreaterEqual(len(GRADED), 2)
        for entry in GRADED:
            with self.subTest(case=entry["id"]):
                defects = conversation_defects(_conversation(entry), TOPOLOGY, ETIQUETTE)
                if entry["expected_etiquette"]:
                    self.assertEqual(defects, [], entry["id"])
                else:
                    self.assertNotEqual(defects, [], entry["id"])

    def test_every_schema_valid_defeating_entry_is_graded(self) -> None:
        """A defeating entry the schema accepts must be caught here or nowhere."""
        for entry in ENTRIES:
            if entry["polarity"] == "defeating" and entry["expected_validity"] == "VALID":
                with self.subTest(case=entry["id"]):
                    self.assertIn("expected_etiquette", entry)
                    self.assertFalse(entry["expected_etiquette"])

    def test_both_polarities_are_present_and_ids_are_unique(self) -> None:
        ids = [entry["id"] for entry in ENTRIES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate fixture id")
        self.assertEqual({entry["polarity"] for entry in ENTRIES}, {"positive", "defeating"})

    def test_every_declared_act_is_exercised_by_some_entry(self) -> None:
        """An act nobody ever speaks in the corpus is an unchecked rule."""
        spoken = {message["act"] for entry in ENTRIES for message in _conversation(entry)}
        unexercised = sorted(set(ETIQUETTE["acts"]) - spoken)
        self.assertEqual(
            unexercised, ["ACCEPT", "ASK", "DISPATCH", "PLAN", "REFUSE", "UNATTESTABLE"],
            "the set of acts with no fixture changed; extend the corpus or update this list")

    def test_every_carriage_duty_is_implemented_by_the_checker(self) -> None:
        """A duty the checker skipped silently would report a pass for an unrun check."""
        probe = {
            "message_schema": "soveraeign-seat-message/v1", "message_id": "msg:probe",
            "sent_at": "2026-08-23T12:00:00Z",
            "speaker": {"seat_id": "seat:worker-1", "seat_type": "work",
                        "actor_id": "probe@1", "actor_kind": "MODEL",
                        "relation_to_subject": "INDEPENDENT"},
            "to_seat": "seat:orchestrator-1", "act": "ATTEST",
            "subject": {"operation_id": "OP-PROBE"}, "body": "probe",
            "standing_proposed": {"from": "BUILT", "to": "WITNESSED"},
            "carries": {"judgement_items": [], "dissents": [], "residuals": [], "stalls": []},
        }
        self.assertEqual(conversation_defects([probe], TOPOLOGY, ETIQUETTE), [])
        etiquette = json.loads(json.dumps(ETIQUETTE))
        etiquette["carriage_duties"].append(
            {"duty": "UNIMPLEMENTED_DUTY", "applies_to_act": "ATTEST", "kinds": [],
             "rule": "a duty this checker has never heard of", "plain_english": "probe"})
        defects = conversation_defects([probe], TOPOLOGY, etiquette)
        self.assertTrue(any("UNIMPLEMENTED_DUTY" in defect for defect in defects),
                        "the checker passed a duty it does not implement")

    def test_the_positive_chain_delivers_every_raised_item_to_the_root(self) -> None:
        """The point of the carriage duty, stated as an assertion rather than a rule."""
        kinds = ("judgement_items", "dissents", "residuals", "stalls")
        to_root = [entry for entry in ENTRIES
                   if entry["polarity"] == "positive"
                   and entry["record"]["to_seat"] == TOPOLOGY["root_seat"]]
        self.assertTrue(to_root, "no positive entry ever addresses the root seat")
        for entry in to_root:
            with self.subTest(case=entry["id"]):
                raised = {item["item_id"] for message in entry.get("context", [])
                          for kind in kinds for item in message["carries"][kind]}
                delivered = {item["item_id"] for kind in kinds
                             for item in entry["record"]["carries"][kind]}
                self.assertTrue(raised)
                self.assertEqual(raised, delivered, "an item raised below never reached root")


if __name__ == "__main__":
    unittest.main()
