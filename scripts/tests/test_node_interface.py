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
        self.assertEqual(self.document["counts"], {
            "declared": 102, "bound": 102, "policy_active": 33,
            "reachable": 2, "observed": 0,
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
            {"name": "sov://asset/ingest-asset"})
        self.assertEqual(request["logical_endpoint"], "sov://registry/resolve")

    def test_affordances_are_derived_across_two_services(self) -> None:
        ingest = self.operation("asset.ingest-asset")
        resolve_registry = self.operation("registry.resolve")
        unavailable_read = self.operation("asset.read-asset")
        self.assertEqual(ingest["affordance"], {
            "kind": "ACTION",
            "reason_code": "EXACT_ROUTE_ACTIVE",
            "explanation": "An exact policy-active service route exposes this operation.",
        })
        self.assertEqual(resolve_registry["affordance"]["kind"], "READ")
        self.assertEqual(resolve_registry["affordance"]["reason_code"],
                         "EXACT_READ_ROUTE_ACTIVE")
        self.assertEqual(unavailable_read["affordance"]["kind"], "INSPECT")
        self.assertEqual(unavailable_read["affordance"]["reason_code"],
                         "ACTIVE_POLICY_HAS_NO_EXACT_ROUTE")
        self.assertIn(
            "scripts/sovnode/affordances.py",
            {source["address"] for source in ingest["sources"]},
        )

    def test_affordance_edit_cannot_make_topology_invokable(self) -> None:
        edited = deepcopy(self.document)
        record = next(item for item in edited["operations"]
                      if item["operation_id"] == "asset.read-asset")
        record["affordance"] = {
            "kind": "ACTION", "reason_code": "EXACT_ROUTE_ACTIVE",
            "explanation": "renderer says yes",
        }
        material = dict(record)
        material.pop("record_digest")
        record["record_digest"] = sha256(json.dumps(
            material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        with self.assertRaises(BindingRefusal) as raised:
            invocation_request(edited, "asset.read-asset", HUMAN, "actor", "scope", {})
        self.assertEqual(raised.exception.code, "AFFORDANCE_DRIFT")

    def test_model_inventory_and_harness_are_declared_omissions_not_capabilities(self) -> None:
        inventory = json.loads(
            (ROOT / "adapters" / "ollama" / "inventory.json").read_text("utf-8"))
        binding = json.loads((ROOT / "adapters" / "ollama" / "bindings" /
                              "qwen3-4b.json").read_text("utf-8"))
        self.assertTrue(any(
            model["model_id"] == binding["model_id"]
            and model["model_version"] == binding["model_version"]
            for model in inventory["models"]
        ))
        self.assertNotIn(
            "invoke_model", {item["operation"] for item in self.document["operations"]})
        self.assertEqual(
            {item["code"] for item in self.document["omissions"]},
            {
                "OBJECT_INSTANCES_NOT_PROJECTED",
                "MODEL_BINDINGS_NOT_PROJECTED",
                "HARNESS_STATE_NOT_PROJECTED",
            },
        )
        self.assertNotIn("HARNESS", {
            item["affordance"]["kind"] for item in self.document["operations"]
        })

    def test_projection_cannot_promote_its_own_status(self) -> None:
        promoted = deepcopy(self.document)
        promoted["status"] = "RATIFIED"
        self.assertTrue(any("status" in defect for defect in validate(promoted, self.schema)))

    def test_changed_raw_source_digest_changes_input_identity(self) -> None:
        moved = deepcopy(self.document["source_digests"])
        moved[0]["digest"] = "0" * 64
        self.assertNotEqual(
            input_state_digest(moved, route_census(), {}),
            self.document["input_state_digest"],
        )

    def test_a_renderer_edit_cannot_activate_an_inactive_operation(self) -> None:
        edited = deepcopy(self.document)
        record = next(item for item in edited["operations"]
                      if item["operation_id"] == "console.resolve-judgement")
        record["facts"]["reachable"] = True
        with self.assertRaises(BindingRefusal) as raised:
            invocation_request(
                edited, "console.resolve-judgement", HUMAN, "actor", "scope", {})
        self.assertEqual(raised.exception.code, "INTERFACE_RECORD_DRIFT")


class HumanModelParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document, defects = rebuild()
        if defects:
            raise RuntimeError(defects)
        cls.record = resolve(cls.document, "asset.ingest-asset")
        cls.proof = prove()

    def test_read_renderings_resolve_same_identity_authority_and_sources(self) -> None:
        human = render_human(self.record)
        model = json.loads(render_model(self.record))
        self.assertIn(self.record["record_digest"][:12], human)
        self.assertEqual(model["record_digest"], self.record["record_digest"])
        self.assertEqual(model["required_authority"], self.record["required_authority"])
        self.assertEqual(model["affordance"], self.record["affordance"])
        self.assertIn("affordance ACTION", human)
        self.assertEqual(model["sources"], self.record["sources"])

    def test_human_and_model_cross_same_governed_action_semantics(self) -> None:
        self.assertTrue(self.proof["same_action_semantics"])
        for binding in (HUMAN, MODEL):
            result = self.proof["actions"][binding]
            self.assertTrue(result["service_receipt_unchanged"])
            self.assertEqual(result["operation_digest"], self.record["record_digest"])
            self.assertEqual(result["required_authority"], "ingest:asset")
            self.assertEqual(result["terminal_outcome"], "COMMITTED")
            self.assertEqual(result["terminal_event"], "asset.ingest")

    def test_human_and_model_resolve_through_same_registry_receipt(self) -> None:
        self.assertTrue(self.proof["same_registry_semantics"])
        record = resolve(self.document, "registry.resolve")
        for binding in (HUMAN, MODEL):
            result = self.proof["registry_reads"][binding]
            self.assertTrue(result["service_receipt_unchanged"])
            self.assertEqual(result["operation_digest"], record["record_digest"])
            self.assertEqual(result["required_authority"], "read:registry")
            self.assertEqual(result["terminal_outcome"], "COMMITTED")
            self.assertEqual(result["terminal_event"], "registry.resolve")
            self.assertEqual(result["resolved_capability"], "asset.ingest-asset")
            self.assertEqual(result["standing_effect"], "NONE")

    def test_governed_no_is_an_actual_refused_receipt(self) -> None:
        self.assertEqual(self.proof["refusal"]["outcome"], "REFUSED")
        self.assertEqual(self.proof["refusal"]["reason_code"], "AUTHORITY_REFUSED")
        self.assertTrue(self.proof["refusal"]["receipt_id"].startswith("entry_"))

    def test_policy_inactive_console_route_is_refused_by_gateway(self) -> None:
        inactive = self.proof["inactive_operation"]
        self.assertFalse(inactive["interface_reachable"])
        self.assertEqual(inactive["outcome"], "REFUSED")
        self.assertEqual(inactive["reason_code"], "TRANSPORT_NOT_ACTIVATED")


if __name__ == "__main__":
    unittest.main()
