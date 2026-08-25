"""Prove service manifests compose into one derived Kernel binding closure.

A service manifest is the authored participant declaration. The paradigm registry
resolves the stable Kernel contract names those manifests already use to governing
source addresses. The closure is disposable and rebuilt from both plus the Kernel
transition table.

Passing establishes evidence for the binding compiler only. It does not ratify the
Root/Kernel/paradigm vocabulary, grant authority, or make the Kernel a runtime service.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402
from sovkernel.kernel_binding import (  # noqa: E402
    binding_defects,
    build,
    closure_defects,
    is_stale,
    load_manifests,
)

CONTRACTS = ROOT / "contracts"
SCHEMA = json.loads((CONTRACTS / "kernel-closure.schema.json").read_text("utf-8"))
PARADIGM_SCHEMA = json.loads((CONTRACTS / "kernel-paradigms.schema.json").read_text("utf-8"))
PARADIGMS = json.loads((CONTRACTS / "kernel-paradigms.json").read_text("utf-8"))
TRANSITIONS = json.loads((CONTRACTS / "kernel-transitions.json").read_text("utf-8"))
MANIFEST_SCHEMA = json.loads((CONTRACTS / "service-manifest.schema.json").read_text("utf-8"))
MANIFESTS, MANIFEST_SOURCES = load_manifests(ROOT)
DERIVED_FROM = MANIFEST_SOURCES + [
    "contracts/kernel-paradigms.json",
    "contracts/kernel-transitions.json",
]


class RepositoryClosure(unittest.TestCase):
    def test_every_service_manifest_is_discovered_without_a_hard_coded_list(self) -> None:
        declared = sorted(path.parents[1].name
                          for path in (ROOT / "services").glob("*/contracts/service.json"))
        self.assertEqual(sorted(MANIFESTS), declared)
        self.assertGreaterEqual(len(MANIFESTS), 8)

    def test_paradigm_registry_satisfies_its_contract_and_sources_resolve(self) -> None:
        self.assertEqual(validate(PARADIGMS, PARADIGM_SCHEMA), [])
        for paradigm in PARADIGMS["paradigms"]:
            for source in paradigm["sources"]:
                with self.subTest(paradigm=paradigm["paradigm"], source=source):
                    self.assertTrue((ROOT / source).is_file())

    def test_manifest_kernel_contract_vocabulary_matches_paradigm_registry(self) -> None:
        """Two machine indexes may exist only while drift between them is defeated."""
        schema_ids = set(MANIFEST_SCHEMA["properties"]["uses_kernel_contracts"]["items"]["enum"])
        paradigm_ids = {entry["paradigm"] for entry in PARADIGMS["paradigms"]}
        self.assertEqual(schema_ids, paradigm_ids)

    def test_current_authored_bindings_have_no_cross_manifest_contradiction(self) -> None:
        self.assertEqual(binding_defects(MANIFESTS, TRANSITIONS, PARADIGMS), [])

    def test_derived_closure_satisfies_its_machine_contract(self) -> None:
        closure = build(MANIFESTS, TRANSITIONS, PARADIGMS, derived_from=DERIVED_FROM)
        self.assertEqual(validate(closure, SCHEMA), [])
        self.assertEqual(
            closure_defects(
                closure, MANIFESTS, TRANSITIONS, PARADIGMS, derived_from=DERIVED_FROM
            ),
            [],
        )

    def test_closure_resolves_each_kernel_paradigm_to_sources_and_participants(self) -> None:
        closure = build(MANIFESTS, TRANSITIONS, PARADIGMS, derived_from=DERIVED_FROM)
        by_id = {entry["paradigm"]: entry for entry in closure["paradigm_usage"]}
        for definition in PARADIGMS["paradigms"]:
            paradigm = definition["paradigm"]
            expected = sorted(
                manifest["service_id"] for manifest in MANIFESTS.values()
                if paradigm in manifest.get("uses_kernel_contracts", [])
            )
            self.assertEqual(by_id[paradigm]["participants"], expected)
            self.assertEqual(by_id[paradigm]["sources"], sorted(definition["sources"]))

    def test_closure_exposes_unmapped_operations_instead_of_inventing_transitions(self) -> None:
        closure = build(MANIFESTS, TRANSITIONS, PARADIGMS, derived_from=DERIVED_FROM)
        declared_without_mapping = sorted(
            f"{manifest['service_id']}.{operation['operation']}"
            for manifest in MANIFESTS.values()
            for operation in manifest["operations"]
            if "kernel_transition" not in operation
        )
        self.assertEqual(closure["unmapped_operations"], declared_without_mapping)
        self.assertTrue(closure["unmapped_operations"],
                        "the current closure unexpectedly claims every operation is mapped")

    def test_closure_goes_stale_when_any_binding_input_moves(self) -> None:
        closure = build(MANIFESTS, TRANSITIONS, PARADIGMS, derived_from=DERIVED_FROM)
        moved = deepcopy(MANIFESTS)
        moved["asset"]["forbids"] = list(moved["asset"]["forbids"]) + ["invented-shortcut"]
        self.assertFalse(is_stale(closure, MANIFESTS, TRANSITIONS, PARADIGMS))
        self.assertTrue(is_stale(closure, moved, TRANSITIONS, PARADIGMS))

        moved_paradigms = deepcopy(PARADIGMS)
        moved_paradigms["paradigms"][0]["description"] += " moved"
        self.assertTrue(is_stale(closure, MANIFESTS, TRANSITIONS, moved_paradigms))


class DefeatingBindings(unittest.TestCase):
    def setUp(self) -> None:
        self.manifests = deepcopy(MANIFESTS)
        self.paradigms = deepcopy(PARADIGMS)

    def defect_codes(self) -> set[str]:
        return {defect.split(":", 1)[0] for defect in
                binding_defects(self.manifests, TRANSITIONS, self.paradigms)}

    def test_a_service_directory_cannot_claim_to_be_another_service(self) -> None:
        self.manifests["asset"]["service_id"] = "registry"
        self.assertIn("SERVICE_ID_DRIFT", self.defect_codes())

    def test_two_services_cannot_both_own_the_same_kernel_type(self) -> None:
        owned = self.manifests["asset"]["owns"][0]
        self.manifests["record"]["owns"] = list(self.manifests["record"]["owns"]) + [owned]
        self.assertIn("MULTIPLE_TYPE_OWNERS", self.defect_codes())

    def test_operation_subject_must_be_owned_by_its_service(self) -> None:
        self.manifests["asset"]["operations"][0]["subject"] = "journal-entry"
        self.assertIn("FOREIGN_SUBJECT", self.defect_codes())

    def test_logical_endpoint_identity_cannot_drift_from_service_and_operation(self) -> None:
        self.manifests["asset"]["operations"][0]["logical_endpoint"] = (
            "sov://registry/ingest-asset"
        )
        self.assertIn("ENDPOINT_IDENTITY_DRIFT", self.defect_codes())

    def test_unknown_transition_cannot_enter_through_one_service_manifest(self) -> None:
        self.manifests["asset"]["operations"][0]["kernel_transition"] = "teleport_state"
        self.assertIn("UNKNOWN_KERNEL_TRANSITION", self.defect_codes())

    def test_unknown_paradigm_cannot_be_privately_invented_by_one_service(self) -> None:
        self.manifests["asset"]["uses_kernel_contracts"] = (
            list(self.manifests["asset"]["uses_kernel_contracts"]) + ["super-authority"]
        )
        self.assertIn("UNKNOWN_KERNEL_PARADIGM", self.defect_codes())

    def test_duplicate_paradigm_definition_is_refused(self) -> None:
        self.paradigms["paradigms"].append(deepcopy(self.paradigms["paradigms"][0]))
        self.assertIn("DUPLICATE_KERNEL_PARADIGM", self.defect_codes())

    def test_unmapped_operation_is_a_visible_gap_not_a_binding_failure(self) -> None:
        operation = self.manifests["asset"]["operations"][0]
        operation.pop("kernel_transition", None)
        self.assertNotIn("UNKNOWN_KERNEL_TRANSITION", self.defect_codes())
        closure = build(
            self.manifests, TRANSITIONS, self.paradigms, derived_from=DERIVED_FROM
        )
        self.assertIn("asset.ingest-asset", closure["unmapped_operations"])


if __name__ == "__main__":
    unittest.main()
