"""Prove the capability map projects the service manifests and refuses what it must.

``scripts/tests/test_contract_fixtures.py`` already proves each fixture ``record``
against ``contracts/capability-map.schema.json``. This module proves the half a schema
cannot express: that the checked-in reference map is a faithful, total, rebuildable
projection of the manifests it names, and that each semantic fixture is defeated by
the check it declares rather than merely labelled defeating.

Passing establishes ``BUILT`` for the contract and its derivation. It witnesses
nothing: no endpoint here is served, and no actor holds any grant this map names.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.capability_map import build, is_stale, map_defects  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402

CONTRACTS = ROOT / "contracts"
FIXTURES = CONTRACTS / "fixtures"
SCHEMA = json.loads((CONTRACTS / "capability-map.schema.json").read_text("utf-8"))
TABLE = json.loads((CONTRACTS / "capability-offices.json").read_text("utf-8"))
REFERENCE = json.loads((FIXTURES / "capability-map.reference.json").read_text("utf-8"))
ENTRIES = json.loads((FIXTURES / "capability-map.fixtures.json").read_text("utf-8"))
GRADED = [entry for entry in ENTRIES if "expected_map_defects" in entry]

MANIFEST_PATHS = sorted((ROOT / "services").glob("*/contracts/service.json"))


def _manifests() -> dict[str, dict]:
    loaded = {}
    for path in MANIFEST_PATHS:
        manifest = json.loads(path.read_text("utf-8"))
        loaded[manifest["service_id"]] = manifest
    return loaded


def _derived_from() -> list[str]:
    addresses = [path.relative_to(ROOT).as_posix() for path in MANIFEST_PATHS]
    addresses.append("contracts/capability-offices.json")
    return addresses


class ReferenceMap(unittest.TestCase):
    """The checked-in map against the manifests it claims to project."""

    def test_the_reference_map_satisfies_its_contract(self) -> None:
        self.assertEqual(validate(REFERENCE, SCHEMA), [])

    def test_the_reference_map_has_no_semantic_defect(self) -> None:
        self.assertEqual(map_defects(REFERENCE, _manifests(), TABLE), [])

    def test_rebuilding_from_the_same_inputs_is_identical(self) -> None:
        """A projection that differs between builds is not a projection."""
        rebuilt = build(_manifests(), TABLE, phase=REFERENCE["phase"],
                        derived_from=_derived_from())
        self.assertEqual(rebuilt, REFERENCE)

    def test_the_map_is_total_over_every_declared_operation(self) -> None:
        """An operation absent from the map is a door nobody governs."""
        mapped = {row["capability_id"] for row in REFERENCE["capabilities"]}
        declared = {f"{service_id}.{entry['operation']}"
                    for service_id, manifest in _manifests().items()
                    for entry in manifest["operations"]}
        self.assertEqual(mapped, declared)

    def test_the_map_goes_stale_when_an_input_moves(self) -> None:
        moved = _manifests()
        moved["asset"] = dict(moved["asset"], standing="WITNESSED")
        self.assertFalse(is_stale(REFERENCE, _manifests(), TABLE))
        self.assertTrue(is_stale(REFERENCE, moved, TABLE))


class PhaseBoundaries(unittest.TestCase):
    """What the current phase forbids, read off the real map rather than the policy."""

    def test_no_external_transport_is_activated_anywhere(self) -> None:
        for row in REFERENCE["capabilities"]:
            for endpoint in row["endpoints"]:
                if endpoint["transport"] in TABLE["external_transports_refused_in_phase"]:
                    with self.subTest(capability=row["capability_id"]):
                        self.assertEqual(endpoint["activation"], "REFUSED_UNCONFIGURED")
                        self.assertEqual(endpoint["refusal_code"], "UNCONFIGURED")

    def test_no_proposed_service_serves_a_live_endpoint(self) -> None:
        for row in REFERENCE["capabilities"]:
            if row["service_standing"] == "PROPOSED":
                for endpoint in row["endpoints"]:
                    with self.subTest(capability=row["capability_id"]):
                        self.assertNotEqual(endpoint["activation"], "ACTIVE")

    def test_no_back_office_capability_is_served_operator_facing(self) -> None:
        facing = {name for name, policy in TABLE["transport_policy"].items()
                  if policy["operator_facing"]}
        for row in REFERENCE["capabilities"]:
            if row["office"] != "BACK":
                continue
            for endpoint in row["endpoints"]:
                if endpoint["transport"] in facing:
                    with self.subTest(capability=row["capability_id"]):
                        self.assertNotEqual(endpoint["activation"], "ACTIVE")

    def test_only_a_human_may_be_asked_to_ratify_judgement(self) -> None:
        """AGENTS.md: only Bdo ratifies judgement, so no model door opens onto it."""
        for row in REFERENCE["capabilities"]:
            if row["required_authority"] == "ratify:judgement":
                with self.subTest(capability=row["capability_id"]):
                    self.assertEqual(row["actor_kinds"], ["HUMAN"])

    def test_at_least_one_capability_is_actually_reachable(self) -> None:
        """A map in which nothing is served would pass every refusal test vacuously."""
        served = [row["capability_id"] for row in REFERENCE["capabilities"]
                  if any(endpoint["activation"] == "ACTIVE" for endpoint in row["endpoints"])]
        self.assertTrue(served, "no capability is served on any transport")


class SemanticFixtures(unittest.TestCase):
    """Each schema-valid defeating fixture must be caught by the check it names."""

    def test_the_fixture_set_carries_semantic_defeats(self) -> None:
        self.assertGreaterEqual(len(GRADED), 5)

    def test_every_graded_fixture_is_defeated_by_its_declared_check(self) -> None:
        for entry in GRADED:
            with self.subTest(fixture=entry["id"]):
                self.assertEqual(validate(entry["record"], SCHEMA), [],
                                 "a semantic fixture must be schema-valid")
                observed = sorted({defect.split(":")[0] for defect in
                                   map_defects(entry["record"], entry["manifests"],
                                               entry["table"])})
                self.assertEqual(observed, sorted(set(entry["expected_map_defects"])))

    def test_the_positive_fixture_carries_no_defect(self) -> None:
        positive = [entry for entry in ENTRIES if entry["polarity"] == "positive"]
        self.assertTrue(positive)
        for entry in positive:
            with self.subTest(fixture=entry["id"]):
                self.assertEqual(validate(entry["record"], SCHEMA), [])


if __name__ == "__main__":
    unittest.main()
