"""Prove the surface grader reads the tree rather than trusting the declaration.

``scripts/sov_publication.py selfcheck`` grades fifteen declared cases against
synthetic contracts. This module proves what that corpus cannot: that the real
checked-in contract covers the real tracked tree, that a finding's holder decides
whether ``check`` fails, and that the queue is stable enough for a loop to drain
one item at a time without re-deciding what the items are.

Passing establishes ``BUILT`` for the grader. It witnesses nothing, and it says
nothing about whether any path is classified correctly - only that the tree and
the declaration are being compared at all.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import sov_publication  # noqa: E402


class ContractCoversTheTree(unittest.TestCase):
    """The declaration must stay complete as the repository grows."""

    def setUp(self) -> None:
        self.contract = sov_publication.load()
        self.paths = sov_publication.tracked()

    def test_every_tracked_top_level_path_is_classified(self) -> None:
        self.assertEqual([], sov_publication.coverage(self.contract, self.paths))

    def test_every_declared_surface_is_one_the_contract_defines(self) -> None:
        declared = set(self.contract["surfaces"])
        for entry in self.contract["paths"]:
            self.assertIn(entry["surface"], declared, entry["path"])

    def test_every_declared_path_states_why(self) -> None:
        for entry in self.contract["paths"]:
            self.assertTrue(entry.get("why"), f"{entry['path']} is classified without a reason")

    def test_no_local_surface_has_tracked_files(self) -> None:
        local = [entry for entry in self.contract["paths"] if entry["surface"] == "LOCAL"]
        self.assertTrue(local, "a contract with no LOCAL entry cannot prove the rule fires")
        leaks = [item for item in sov_publication.surfaces(self.contract, self.paths)
                 if item["check"] == "LOCAL_TRACKED"]
        self.assertEqual([], leaks)

    def test_every_derived_path_names_a_builder_and_a_check_that_exist(self) -> None:
        unchecked = [item for item in sov_publication.surfaces(self.contract, self.paths)
                     if item["check"] == "DERIVED_UNCHECKED"]
        self.assertEqual([], unchecked)


class HolderDecidesTheGate(unittest.TestCase):
    """An owner-held finding is reported; only a sov-held finding is a defect."""

    def test_an_owner_held_route_gap_does_not_fail_the_gate(self) -> None:
        contract = {"routes": [{"audience": "person", "document": "CONTRACT.md",
                                "must_name": ["zzz-absent"], "must_not_name": [],
                                "owner_held": ["zzz-absent"]}]}
        found = sov_publication.routes(contract)
        self.assertEqual(1, len(found))
        self.assertEqual(sov_publication.OWNER, found[0]["holder"])

    def test_the_same_gap_without_the_owner_hold_is_a_defect(self) -> None:
        contract = {"routes": [{"audience": "person", "document": "CONTRACT.md",
                                "must_name": ["zzz-absent"], "must_not_name": []}]}
        found = sov_publication.routes(contract)
        self.assertEqual(sov_publication.SOV, found[0]["holder"])


class QueueIsDrainable(unittest.TestCase):
    """A loop needs stable ids and a finite queue, or it re-decides every iteration."""

    def setUp(self) -> None:
        self.found = sov_publication.audit(sov_publication.load(), sov_publication.tracked())

    def test_every_finding_carries_a_stable_id_and_a_holder(self) -> None:
        for item in self.found:
            self.assertEqual(f"{item['check']}:{item['path']}", item["id"])
            self.assertIn(item["holder"], (sov_publication.SOV, sov_publication.OWNER))

    def test_finding_ids_are_unique(self) -> None:
        ids = [item["id"] for item in self.found]
        self.assertEqual(sorted(set(ids)), sorted(ids))

    def test_the_queue_serialises(self) -> None:
        json.dumps(self.found)

    def test_the_audit_is_stable_across_two_readings(self) -> None:
        again = sov_publication.audit(sov_publication.load(), sov_publication.tracked())
        self.assertEqual([item["id"] for item in self.found], [item["id"] for item in again])


class RefusalsFire(unittest.TestCase):
    """The declared corpus must stay green, so an empty finding list means something."""

    def test_selfcheck_passes(self) -> None:
        self.assertEqual(0, sov_publication.selfcheck())

    def test_a_missing_contract_is_a_defect_rather_than_a_clean_reading(self) -> None:
        with self.assertRaises(sov_publication.ContractError):
            sov_publication.load(ROOT / "contracts" / "does-not-exist.json")


if __name__ == "__main__":
    unittest.main()
