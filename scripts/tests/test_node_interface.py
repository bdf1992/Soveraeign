"""Contract, parity, staleness, and action proof for the derived Node Interface."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from sovkernel.jsonschema import validate  # noqa: E402
from sovkernel.node_interface import input_state_digest  # noqa: E402
from sovnode.bindings import (  # noqa: E402
    HUMAN, MODEL, BindingRefusal, invocation_request, render_human, render_model, resolve,
)
from sovnode.composition import route_census  # noqa: E402
from sovnode.interface_inputs import rebuild  # noqa: E402
from sovnode.proof import run as prove  # noqa: E402


class ProjectionFacts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, cls.defects = rebuild()
        cls.schema = json.loads(
            (ROOT / "contracts" / "node-interface.schema.json").read_text("utf-8"))

    def operation(self, operation_id: str) -> dict:
        return resolve(self.document, operation_id)

    def test_current_projection_satisfies_contract_and_semantics(self) -> None:
        self.assertEqual(self.defects, [])
        self.assertEqual(validate(self.document, self.schema), [])
        self.assertEqual(self.document["status"], "PROPOSED")

    def test_evidence_layers_remain_independent(self) -> None:
        # record.project-evidence adds one declared, bound and policy-active read.
        # It is intentionally not a new transport route or observation, so those
        # two evidence layers remain unchanged while the first three advance.
        self.assertEqual(self.document["counts"], {
            "declared": 135, "bound": 135, "policy_active": 47,
            "reachable": 5, "observed": 0,
        })
        self.assertEqual(self.operation("asset.ingest-asset")["facts"], {
            "declared": True, "bound": True, "policy_active": True,
            "reachable": True, "observed": False,
        })

    def test_built_read_asset_contradiction_stays_visible(self) -> None:
        record = self.operation("asset.read-asset")
        self.assertEqual(record["standing"], "BUILT")
        self.assertTrue(record["facts"]["policy_active"])
        self.assertFalse(record["facts"]["reachable"])
        self.assertIn(record["operation_id"],
                      self.document["seams"]["built_not_reachable"])

    def test_judgement_choices_are_visible_but_not_activated(self) -> None:
        record = self.operation("console.resolve-judgement")
        self.assertEqual(record["legal_choices"], ["ACCEPTED", "STRUCK", "DEFERRED"])
        self.assertFalse(record["facts"]["policy_active"])
        self.assertFalse(record["facts"]["reachable"])

    def test_registry_resolve_is_bound_active_and_reachable_but_unobserved(self) -> None:
        record = self.operation("registry.resolve")
        self.assertTrue(record["facts"]["bound"])
        self.assertTrue(record["facts"]["policy_active"])
        self.assertTrue(record["facts"]["reachable"])
        self.assertFalse(record["facts"]["observed"])
        request = invocation_request(
            self.document, "registry.resolve", HUMAN, "reader", "registry:any",
            {"name": "sov://asset/ingest-asset"}, session_id="session:test",
            session_binding_id="host:test", principal_id=None)
        self.assertEqual(request["logical_endpoint"], "sov://registry/resolve")

    def test_route_affordances_are_actor_neutral_across_four_services(self) -> None:
        ingest = self.operation("asset.ingest-asset")
        read_version = self.operation("asset.read-version")
        read_thread = self.operation("console.read-thread")
        resolve_registry = self.operation("registry.resolve")
        for record in (ingest, read_version, read_thread, resolve_registry):
            self.assertEqual(record["affordance"], "ACTION" if record["crud"] != "READ" else "READ")
            self.assertNotIn("actor", record["affordance"].lower())

    def test_interface_input_digest_binds_all_sources(self) -> None:
        digest, sources = input_state_digest(ROOT)
        self.assertEqual(self.document["input_state_digest"], digest)
        self.assertGreater(len(sources), 1)
        self.assertTrue(all(item["digest"].startswith("sha256:") for item in sources))

    def test_reference_file_is_not_an_input_to_its_own_digest(self) -> None:
        _, sources = input_state_digest(ROOT)
        paths = {item["path"] for item in sources}
        self.assertNotIn("contracts/fixtures/node-interface.reference.json", paths)


class RebuildRefusals(unittest.TestCase):
    def test_a_route_not_in_the_manifest_is_a_defect(self) -> None:
        original = route_census
        try:
            import sovnode.interface_inputs as inputs
            inputs.route_census = lambda: {"asset": {"invented-route"}}
            _, defects = rebuild()
        finally:
            inputs.route_census = original
        self.assertTrue(any("invented-route" in defect for defect in defects))


class BindingParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, _ = rebuild()

    def test_human_and_model_resolve_the_same_operation(self) -> None:
        for operation_id in ("asset.ingest-asset", "console.read-thread", "registry.resolve"):
            human = render_human(resolve(self.document, operation_id))
            model = render_model(resolve(self.document, operation_id))
            self.assertEqual(human["operation_id"], model["operation_id"])
            self.assertEqual(human["required_authority"], model["required_authority"])
            self.assertEqual(human["effect_class"], model["effect_class"])

    def test_unknown_operation_refuses(self) -> None:
        with self.assertRaises(BindingRefusal):
            resolve(self.document, "no.such-operation")


class ActionProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, _ = rebuild()

    def test_proof_over_unreachable_operation_refuses(self) -> None:
        result = prove(self.document, "asset.read-asset", actor_kind=HUMAN)
        self.assertFalse(result["proved"])
        self.assertIn("NOT_REACHABLE", result["refusals"])

    def test_proof_does_not_turn_policy_into_authority(self) -> None:
        result = prove(self.document, "asset.ingest-asset", actor_kind=MODEL)
        self.assertFalse(result["proved"])
        self.assertIn("AUTHORITY_UNRESOLVED", result["refusals"])


if __name__ == "__main__":
    unittest.main()
