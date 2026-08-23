"""Execute the seat-registry fixtures: schema validity and the rooted-tree guard.

The schema owns field shape; the tree guard is semantic (decisions/0020): every
seat except exactly one root has exactly one owner edge that resolves, and every
chain terminates at the declared root without a cycle. Passing establishes
``BUILT`` for the contract only; the topology itself is a proposal.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sovkernel.jsonschema import validate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "contracts" / "seat-registry.schema.json").read_text("utf-8"))
FIXTURES = json.loads(
    (ROOT / "contracts" / "fixtures" / "seat-registry.fixtures.json").read_text("utf-8"))


def rooted_tree_defects(registry: dict) -> list[str]:
    """Semantic guard: one root, resolving owner edges, every chain ends at the root."""
    defects: list[str] = []
    seats = {seat["seat_id"]: seat for seat in registry.get("seats", [])}
    declared_root = registry.get("root_seat")
    roots = [seat_id for seat_id, seat in seats.items() if seat.get("seat_type") == "root"]
    if roots != [declared_root]:
        defects.append(f"roots {roots} do not match the declared root {declared_root!r}")
    for seat_id, seat in seats.items():
        if seat.get("owner_seat") is None:
            if seat_id != declared_root:
                defects.append(f"{seat_id}: ownerless seat that is not the declared root")
            continue
        seen, owner = {seat_id}, seat.get("owner_seat")
        while owner is not None:
            if owner not in seats:
                defects.append(f"{seat_id}: owner chain names missing seat {owner}")
                break
            if owner in seen:
                defects.append(f"{seat_id}: owner chain cycles at {owner}")
                break
            seen.add(owner)
            owner = seats[owner].get("owner_seat")
        else:
            if declared_root not in seen:
                defects.append(f"{seat_id}: owner chain does not reach the root")
    return defects


class SeatRegistryFixtures(unittest.TestCase):
    def test_every_fixture_matches_its_declared_expectation(self) -> None:
        self.assertGreaterEqual(len(FIXTURES), 2)
        for case in FIXTURES:
            with self.subTest(case=case["id"]):
                defects = validate(case["record"], SCHEMA)
                if case["expected_validity"] == "VALID":
                    self.assertEqual(defects, [], case["id"])
                else:
                    self.assertNotEqual(defects, [], case["id"])
                if "expected_rooted_tree" in case:
                    tree_defects = rooted_tree_defects(case["record"])
                    if case["expected_rooted_tree"]:
                        self.assertEqual(tree_defects, [], case["id"])
                    else:
                        self.assertNotEqual(tree_defects, [], case["id"])

    def test_fixture_hygiene(self) -> None:
        ids = [case["id"] for case in FIXTURES]
        self.assertEqual(len(ids), len(set(ids)), "duplicate fixture id")
        polarities = {case["polarity"] for case in FIXTURES}
        self.assertEqual(polarities, {"positive", "defeating"})
        for case in FIXTURES:
            if case["polarity"] == "defeating":
                self.assertTrue(case.get("defeats"), case["id"])

    def test_positive_registry_is_the_current_topology(self) -> None:
        record = FIXTURES[0]["record"]
        seats = {seat["seat_id"]: seat for seat in record["seats"]}
        root = seats[record["root_seat"]]
        self.assertEqual(root["occupant"]["actor_kind"], "HUMAN")
        self.assertIsNone(root["owner_seat"])
        self.assertIn("JUDGEMENT", root["settles"])
        workers = [seat for seat in seats.values() if seat["seat_type"] == "work"]
        self.assertTrue(all(seat["settles"] == [] for seat in workers),
                        "a work seat settles nothing")


if __name__ == "__main__":
    unittest.main()
