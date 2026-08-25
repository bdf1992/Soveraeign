"""Defeating and crossing tests for the first Registry Horizontal slice."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
for service in ("record", "registry"):
    sys.path.insert(0, str(ROOT / "services" / service / "src"))

from soveraeign_record_service import RecordService  # noqa: E402
from soveraeign_registry_service import (  # noqa: E402
    RegistryIndexError, RegistryRoutes, RegistryService, build_operation_index,
)
from soveraeign_registry_service import index as registry_index  # noqa: E402
from sovkernel.closure_inputs import rebuild as rebuild_closure  # noqa: E402
from sovkernel import closure_inputs  # noqa: E402
from sovkernel.kernel_sources import load_source_digests  # noqa: E402


def inputs() -> tuple[dict, dict, dict, list[dict[str, str]]]:
    closure, manifests, _, _, closure_sources, defects = rebuild_closure(ROOT)
    if defects:
        raise RuntimeError(defects)
    addresses = [item["address"] for item in closure_sources]
    addresses.append("contracts/capability-offices.json")
    sources, defects = load_source_digests(ROOT, addresses)
    if defects:
        raise RuntimeError(defects)
    policy = json.loads((ROOT / "contracts" / "capability-offices.json").read_text("utf-8"))
    return closure, manifests, policy, sources


class RegistryResolution(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.record = RecordService(Path(self.tmp.name) / "record")
        closure, manifests, policy, sources = inputs()
        self.closure = closure
        self.manifests = manifests
        self.policy = policy
        self.sources = sources
        self.current = {item["address"]: item["digest"] for item in sources}
        self.service = RegistryService(
            self.record, ROOT, closure, manifests, policy, sources,
            digest_reader=self.current.get)

    def tearDown(self) -> None:
        self.record.close()
        self.tmp.cleanup()

    def test_resolve_points_to_owning_sources_and_grants_no_standing(self) -> None:
        receipt = self.service.resolve("sov://asset/ingest-asset", "reader")
        self.assertEqual(receipt["kind"], "RECEIPT")
        self.assertEqual(receipt["payload"]["outcome"], "COMMITTED")
        self.assertEqual(receipt["payload"]["event"], "registry.resolve")
        detail = receipt["payload"]["detail"]
        resolution = detail["resolution"]
        self.assertEqual(resolution["capability_id"], "asset.ingest-asset")
        self.assertEqual(resolution["required_authority"], "ingest:asset")
        self.assertEqual(resolution["standing_effect"], "NONE")
        self.assertRegex(resolution["record_digest"], "^[0-9a-f]{64}$")
        self.assertEqual(detail["commit_semantics"], "DERIVED")
        self.assertEqual(
            [source["address"] for source in resolution["sources"]],
            ["services/asset/contracts/service.json",
             "contracts/capability-offices.json"],
        )
        self.assertEqual(self.record.entries(), [receipt])

    def test_alias_resolves_to_same_derived_record(self) -> None:
        endpoint = self.service.resolve("sov://asset/ingest-asset", "reader")
        capability = self.service.resolve("asset.ingest-asset", "reader")
        self.assertEqual(
            endpoint["payload"]["detail"]["resolution"]["record_digest"],
            capability["payload"]["detail"]["resolution"]["record_digest"],
        )

    def test_unknown_name_is_a_service_owned_refused_receipt(self) -> None:
        receipt = self.service.resolve("sov://unknown/operation", "reader")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(receipt["payload"]["detail"]["reason_code"], "NAME_UNKNOWN")

    def test_changed_source_refuses_before_answering(self) -> None:
        address = "services/asset/contracts/service.json"
        self.current[address] = "0" * 64
        receipt = self.service.resolve("sov://asset/ingest-asset", "reader")
        detail = receipt["payload"]["detail"]
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(detail["reason_code"], "INDEX_STALE")
        self.assertEqual(detail["source_drift"][0]["address"], address)
        self.assertNotIn("resolution", detail)

    def test_missing_source_is_visible_as_index_stale(self) -> None:
        self.current.pop("contracts/capability-offices.json")
        receipt = self.service.resolve("asset.ingest-asset", "reader")
        drift = receipt["payload"]["detail"]["source_drift"]
        self.assertTrue(any(item["actual"] is None for item in drift))

    def test_route_keeps_checked_actor_out_of_domain_arguments(self) -> None:
        routes = RegistryRoutes(self.service)
        with self.assertRaises(ValueError):
            routes.call("resolve", {
                "name": "asset.ingest-asset", "actor": "spoof",
            }, "checked-actor")

    def test_route_census_and_arguments_are_service_owned(self) -> None:
        self.assertEqual(RegistryRoutes.operation_ids(), ("resolve",))
        self.assertEqual(RegistryRoutes.argument_contract("resolve"), {
            "required": ("name",), "optional": (),
        })

    def test_route_returns_the_registry_terminal_receipt(self) -> None:
        receipt = RegistryRoutes(self.service).call(
            "resolve", {"name": "asset.ingest-asset"}, "checked-actor")
        self.assertEqual(receipt["actor"], "checked-actor")
        self.assertEqual(receipt["payload"]["event"], "registry.resolve")

    def test_route_refuses_unknown_operation_and_bad_name_shapes(self) -> None:
        routes = RegistryRoutes(self.service)
        with self.assertRaises(KeyError):
            routes.call("read-entry", {"name": "asset.ingest-asset"}, "actor")
        for arguments in ({}, {"name": ""}, {"name": 3},
                          {"name": "asset.ingest-asset", "extra": True}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                routes.call("resolve", arguments, "actor")

    def test_default_reader_accepts_the_exact_repository_sources(self) -> None:
        service = RegistryService(
            self.record, ROOT, self.closure, self.manifests, self.policy, self.sources)
        receipt = service.resolve("asset.ingest-asset", "reader")
        self.assertEqual(receipt["payload"]["outcome"], "COMMITTED")

    def test_default_reader_refuses_absolute_and_escaping_source_addresses(self) -> None:
        for address in ("/outside", "../outside"):
            with self.subTest(address=address):
                sources = self.sources + [{"address": address, "digest": "0" * 64}]
                service = RegistryService(
                    self.record, ROOT, self.closure, self.manifests, self.policy, sources)
                receipt = service.resolve("asset.ingest-asset", "reader")
                drift = receipt["payload"]["detail"]["source_drift"]
                item = next(item for item in drift if item["address"] == address)
                self.assertIsNone(item["actual"])

    def test_default_reader_refuses_a_missing_repository_source(self) -> None:
        address = "contracts/fixtures/definitely-missing.json"
        sources = self.sources + [{"address": address, "digest": "0" * 64}]
        service = RegistryService(
            self.record, ROOT, self.closure, self.manifests, self.policy, sources)
        receipt = service.resolve("asset.ingest-asset", "reader")
        drift = receipt["payload"]["detail"]["source_drift"]
        item = next(item for item in drift if item["address"] == address)
        self.assertIsNone(item["actual"])


class RegistryIndexDefeaters(unittest.TestCase):
    def test_registry_record_digest_is_independent_of_mapping_order(self) -> None:
        forward = {"a": 1, "b": 2}
        reverse = {"b": 2, "a": 1}
        self.assertEqual(registry_index._digest(forward), registry_index._digest(reverse))

    def test_kernel_loader_refuses_a_snapshot_that_moves_between_reads(self) -> None:
        closure, manifests, policy, sources = inputs()
        transitions = json.loads(
            (ROOT / "contracts" / "kernel-transitions.json").read_text("utf-8"))
        paradigms = json.loads(
            (ROOT / "contracts" / "kernel-paradigms.json").read_text("utf-8"))
        first = (closure, manifests, transitions, paradigms, sources, [])
        moved = deepcopy(closure)
        moved["input_state_digest"] = "0" * 64
        second = (moved, manifests, transitions, paradigms, sources, [])
        with patch.object(closure_inputs, "_rebuild_once", side_effect=[first, second]):
            _, _, _, _, _, defects = closure_inputs.rebuild(ROOT)
        self.assertEqual(defects, [
            "SOURCE_SNAPSHOT_UNSTABLE: Kernel inputs changed while closure was rebuilt",
        ])

    def test_two_operations_cannot_claim_the_same_name(self) -> None:
        closure, manifests, policy, sources = inputs()
        moved_closure, moved_manifests = deepcopy(closure), deepcopy(manifests)
        asset = next(item for item in moved_closure["participants"]
                     if item["service_id"] == "asset")
        second = asset["operations"][1]
        second["logical_endpoint"] = "sov://asset/ingest-asset"
        detail = next(item for item in moved_manifests["asset"]["operations"]
                      if item["operation"] == second["operation"])
        detail["logical_endpoint"] = second["logical_endpoint"]
        with self.assertRaisesRegex(RegistryIndexError, "name collision"):
            build_operation_index(moved_closure, moved_manifests, policy, sources)

    def test_index_refuses_an_operation_without_authored_policy(self) -> None:
        closure, manifests, policy, sources = inputs()
        policy = deepcopy(policy)
        del policy["assignments"]["asset.ingest-asset"]
        with self.assertRaisesRegex(RegistryIndexError, "no authored detail or policy"):
            build_operation_index(closure, manifests, policy, sources)

    def test_index_names_only_the_manifest_operation_the_closure_omits(self) -> None:
        closure, manifests, policy, sources = inputs()
        closure = deepcopy(closure)
        asset = next(item for item in closure["participants"]
                     if item["service_id"] == "asset")
        asset["operations"] = [item for item in asset["operations"]
                               if item["capability_id"] != "asset.ingest-asset"]
        with self.assertRaises(RegistryIndexError) as raised:
            build_operation_index(closure, manifests, policy, sources)
        self.assertEqual(
            str(raised.exception),
            "closure omits manifest operations: ['asset.ingest-asset']",
        )


if __name__ == "__main__":
    unittest.main()
