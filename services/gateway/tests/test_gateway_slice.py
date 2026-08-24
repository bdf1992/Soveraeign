from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Callable
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "gateway" / "src"))
sys.path.insert(0, str(ROOT / "services" / "asset" / "src"))
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_asset_service import AssetService  # noqa: E402
from soveraeign_asset_service.routes import AssetRoutes  # noqa: E402
from soveraeign_console_service import ConsoleService  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
from soveraeign_gateway_service import Gateway, load_surface  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402


class GatewayVerticalSlice(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.record = RecordService(self.root / "record")
        self.console = ConsoleService(self.record, self.root / "console", "node:test")
        self.asset = AssetService(self.root / "asset")
        self.capability_map, self.manifests, self.capability_table = load_surface(ROOT)
        self.gateway = self.new_gateway()

    def new_gateway(self, capability_map: dict | None = None,
                    manifests: dict | None = None,
                    authority: Callable[[str, str, str], str] | None = None,
                    routes: dict | None = None) -> Gateway:
        if authority is None:
            authority = lambda actor, capability, scope: console_authority.check(
                self.record.reconstruct(), actor, capability, scope)
        if routes is None:
            routes = {"asset:in-process": AssetRoutes(self.asset).call}
        return Gateway(
            self.record, capability_map or self.capability_map,
            manifests or self.manifests, self.capability_table,
            authority, routes, authority_denials=(AuthorityRefused,),
        )

    def tearDown(self) -> None:
        self.asset.close()
        self.record.close()
        self.tmp.cleanup()

    def source(self, name: str, data: bytes = b"gateway slice\n") -> Path:
        path = self.root / name
        path.write_bytes(data)
        return path

    def request(self, actor: str, actor_kind: str, path: Path, scope: str) -> dict:
        return {
            "actor": actor,
            "actor_kind": actor_kind,
            "logical_endpoint": "sov://asset/ingest-asset",
            "transport": "IN_PROCESS",
            "scope": scope,
            "arguments": {"path": str(path), "label": "Gateway Slice"},
        }

    def detail(self, receipt: dict) -> dict:
        return receipt["payload"]["detail"]

    def reason(self, receipt: dict) -> str | None:
        return self.detail(receipt).get("reason_code")

    def gateway_events(self, record_kind: str) -> list[dict]:
        return [entry for entry in self.record.entries()
                if entry["kind"] == "EVENT"
                and entry["payload"].get("record_kind") == record_kind]

    def grant_ingest(self, actor: str = "operator", scope: str | None = None) -> str:
        scope = scope or f"asset:new:{actor}"
        self.console.grant(actor, "ingest:asset", scope)
        return scope

    def test_authority_refusal_is_durable_and_asset_never_sees_the_call(self) -> None:
        before = list(self.asset.receipts())
        refused = self.gateway.dispatch(
            self.request("mallory", "MODEL", self.source("denied.txt"), "asset:new"))

        self.assertEqual(refused["kind"], "RECEIPT")
        self.assertEqual(refused["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.reason(refused), "AUTHORITY_REFUSED")
        self.assertEqual(self.detail(refused)["failure_class"], "GOVERNED_REFUSAL")
        self.assertEqual(self.asset.receipts(), before)
        self.assertEqual(self.record.entry(refused["entry_id"]), refused)
        checks = self.gateway_events("gateway-authority-check")
        self.assertEqual(checks[-1]["payload"]["decision"], "REFUSED")

    def test_authority_reader_failure_is_not_counterfeited_as_denial(self) -> None:
        def broken_reader(*_: str) -> str:
            raise RuntimeError("authority journal unavailable")

        gateway = self.new_gateway(authority=broken_reader)
        failed = gateway.dispatch(
            self.request("operator", "HUMAN", self.source("authority-fault.txt"), "asset:new"))

        self.assertEqual(failed["payload"]["outcome"], "FAILED")
        self.assertEqual(self.reason(failed), "AUTHORITY_CHECK_FAILED")
        self.assertEqual(self.detail(failed)["failure_class"], "OPERATIONAL_FAULT")
        self.assertEqual(self.detail(failed)["error_type"], "RuntimeError")
        self.assertEqual(self.asset.receipts(), [])
        self.assertEqual(self.gateway_events("gateway-authority-check")[-1]["payload"]["decision"],
                         "FAILED")

    def test_human_and_model_take_same_kernel_path_and_get_service_receipts_unchanged(self) -> None:
        for actor, actor_kind in (("operator", "HUMAN"), ("local-model", "MODEL")):
            with self.subTest(actor_kind=actor_kind):
                scope = self.grant_ingest(actor)
                returned = self.gateway.dispatch(
                    self.request(actor, actor_kind, self.source(f"{actor}.txt"), scope))

                durable = self.asset.receipts()[-1]
                self.assertEqual(returned, durable)
                self.assertEqual(returned["outcome"], "COMMITTED")
                self.assertEqual(returned["event"], "asset.ingest")
                self.assertEqual(returned["actor"], actor)

        routes = self.gateway_events("gateway-routing-record")
        self.assertEqual(len(routes), 2)
        self.assertEqual({entry["payload"]["route_address"] for entry in routes},
                         {"asset:in-process"})
        self.assertEqual(len(self.gateway_events("gateway-capability-resolution")), 2)
        self.assertEqual(len(self.gateway_events("gateway-authority-check")), 2)
        returned_records = self.gateway_events("gateway-returned-receipt")
        self.assertEqual(len(returned_records), 2)
        self.assertEqual({entry["payload"]["terminal_outcome"] for entry in returned_records},
                         {"COMMITTED"})
        gateway_terminal = [entry for entry in self.record.entries()
                            if entry["kind"] == "RECEIPT"
                            and entry["payload"].get("event") == "gateway.return-receipt"]
        self.assertEqual(gateway_terminal, [])

    def test_malformed_request_has_request_record_before_refusal(self) -> None:
        refused = self.gateway.dispatch({"actor": "operator"})
        self.assertEqual(refused["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.reason(refused), "MALFORMED_REQUEST")
        requests = self.gateway_events("gateway-request")
        self.assertEqual(len(requests), 1)
        self.assertEqual(self.detail(refused)["request_entry_id"], requests[0]["entry_id"])
        self.assertEqual(self.record.entry(refused["entry_id"]), refused)

    def test_unknown_sov_operation_is_not_invented(self) -> None:
        request = self.request("operator", "HUMAN", self.source("unknown.txt"), "asset:new")
        request["logical_endpoint"] = "sov://asset/not-a-real-operation"
        refused = self.gateway.dispatch(request)
        self.assertEqual(self.reason(refused), "ENDPOINT_UNKNOWN")
        self.assertEqual(self.asset.receipts(), [])
        self.assertEqual(self.gateway_events("gateway-authority-check"), [])

    def test_stale_capability_map_refuses_before_authority_or_service(self) -> None:
        stale = deepcopy(self.capability_map)
        stale["input_state_digest"] = "0" * 64
        gateway = self.new_gateway(capability_map=stale)
        request = self.request("operator", "HUMAN", self.source("stale.txt"), "asset:new")
        refused = gateway.dispatch(request)
        self.assertEqual(self.reason(refused), "ENDPOINT_UNKNOWN")
        self.assertEqual(self.detail(refused)["diagnostic_code"], "CAPABILITY_MAP_STALE")
        self.assertEqual(self.asset.receipts(), [])
        self.assertEqual(self.gateway_events("gateway-authority-check"), [])

    def test_capability_projection_tamper_fails_closed_even_with_fresh_input_digest(self) -> None:
        mutations = {
            "required_authority": lambda row: row.__setitem__("required_authority", "route:anything"),
            "actor_kinds": lambda row: row.__setitem__("actor_kinds", ["SYSTEM"]),
            "effect_class": lambda row: row.__setitem__("effect_class", "EXTERNAL_WORLD"),
            "standing": lambda row: row.__setitem__("service_standing", "PROPOSED"),
            "route_address": lambda row: row["endpoints"][0].__setitem__("address", "evil:route"),
            "activation": lambda row: row["endpoints"][0].__setitem__(
                "activation", "DECLARED_NOT_ACTIVATED"),
        }
        for label, mutate in mutations.items():
            with self.subTest(field=label):
                tampered = deepcopy(self.capability_map)
                row = next(row for row in tampered["capabilities"]
                           if row["capability_id"] == "asset.ingest-asset")
                mutate(row)
                gateway = self.new_gateway(capability_map=tampered)
                failed = gateway.dispatch(
                    self.request("operator", "HUMAN", self.source(f"tamper-{label}.txt"),
                                 "asset:new"))
                self.assertEqual(failed["payload"]["outcome"], "FAILED")
                self.assertEqual(self.reason(failed), "CAPABILITY_MAP_INVALID")
                self.assertEqual(self.detail(failed)["failure_class"], "OPERATIONAL_FAULT")
                self.assertEqual(self.asset.receipts(), [])

    def test_http_stays_refused_in_phase_one(self) -> None:
        request = self.request("operator", "HUMAN", self.source("http.txt"), "asset:new")
        request["transport"] = "HTTP"
        refused = self.gateway.dispatch(request)
        self.assertEqual(self.reason(refused), "TRANSPORT_NOT_ACTIVATED")
        self.assertEqual(self.asset.receipts(), [])

    def test_resource_consumption_stays_outside_the_slice(self) -> None:
        actor, scope = "operator", "asset:existing"
        self.console.grant(actor, "request:derivative", scope)
        request = {
            "actor": actor,
            "actor_kind": "HUMAN",
            "logical_endpoint": "sov://asset/request-derivative",
            "transport": "IN_PROCESS",
            "scope": scope,
            "arguments": {"asset_id": "unused", "version_id": "unused"},
        }
        refused = self.gateway.dispatch(request)
        self.assertEqual(self.reason(refused), "EFFECT_CLASS_REFUSED")
        self.assertEqual(self.asset.receipts(), [])

    def test_active_declared_endpoint_without_local_binding_is_service_unreachable(self) -> None:
        scope = self.grant_ingest()
        gateway = self.new_gateway(routes={})
        refused = gateway.dispatch(
            self.request("operator", "HUMAN", self.source("unbound.txt"), scope))
        self.assertEqual(refused["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.reason(refused), "SERVICE_UNREACHABLE")
        self.assertEqual(self.asset.receipts(), [])

    def test_gateway_rejects_client_attribution_override_before_authority_or_service(self) -> None:
        request = self.request("operator", "HUMAN", self.source("spoof.txt"), "asset:new")
        request["arguments"]["actor"] = "mallory"
        refused = self.gateway.dispatch(request)
        self.assertEqual(self.reason(refused), "MALFORMED_REQUEST")
        self.assertEqual(self.detail(refused)["diagnostic_code"], "ACTOR_ATTRIBUTION_CONFLICT")
        self.assertEqual(self.asset.receipts(), [])
        self.assertEqual(self.gateway_events("gateway-authority-check"), [])

    def test_asset_route_still_owns_operation_argument_shape(self) -> None:
        route = AssetRoutes(self.asset)
        with self.assertRaises(ValueError):
            route.call("ingest-asset", {
                "path": str(self.source("bad-asset-argument.txt")),
                "label": "Attribution",
                "domain_specific_unknown": "no",
            }, "operator")
        self.assertEqual(self.asset.receipts(), [])

    def test_service_exception_is_operational_fault_not_governed_refusal(self) -> None:
        scope = self.grant_ingest()

        def broken_route(*_: object) -> dict:
            raise RuntimeError("service exploded")

        gateway = self.new_gateway(routes={"asset:in-process": broken_route})
        failed = gateway.dispatch(
            self.request("operator", "HUMAN", self.source("service-fault.txt"), scope))
        self.assertEqual(failed["payload"]["outcome"], "FAILED")
        self.assertEqual(self.reason(failed), "SERVICE_EXECUTION_FAILED")
        self.assertEqual(self.detail(failed)["failure_class"], "OPERATIONAL_FAULT")
        self.assertIn("routing_entry_id", self.detail(failed))
        self.assertEqual(self.asset.receipts(), [])

    def test_missing_terminal_receipt_is_governed_refusal_after_routing(self) -> None:
        scope = self.grant_ingest()
        gateway = self.new_gateway(
            routes={"asset:in-process": lambda *_: {"executor": "returned"}})
        refused = gateway.dispatch(
            self.request("operator", "HUMAN", self.source("no-receipt.txt"), scope))
        self.assertEqual(refused["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.reason(refused), "RECEIPT_MISSING")
        self.assertEqual(self.detail(refused)["failure_class"], "GOVERNED_REFUSAL")
        self.assertIn("routing_entry_id", self.detail(refused))
        self.assertEqual(self.asset.receipts(), [])

    def test_terminal_receipt_actor_must_match_checked_actor(self) -> None:
        scope = self.grant_ingest()
        spoofed = {"id": "rcpt_spoofed", "outcome": "COMMITTED",
                   "event": "asset.ingest", "actor": "mallory"}
        gateway = self.new_gateway(routes={"asset:in-process": lambda *_: spoofed})
        failed = gateway.dispatch(
            self.request("operator", "HUMAN", self.source("receipt-spoof.txt"), scope))
        self.assertEqual(failed["payload"]["outcome"], "FAILED")
        self.assertEqual(self.reason(failed), "SERVICE_ATTRIBUTION_MISMATCH")
        self.assertEqual(self.detail(failed)["failure_class"], "OPERATIONAL_FAULT")
        self.assertEqual(self.asset.receipts(), [])

    def test_service_terminal_refusal_is_returned_unchanged_not_promoted_to_success(self) -> None:
        scope = self.grant_ingest()
        terminal = {"id": "rcpt_service_refusal", "outcome": "REFUSED",
                    "event": "asset.ingest", "actor": "operator"}
        gateway = self.new_gateway(routes={"asset:in-process": lambda *_: terminal})
        returned = gateway.dispatch(
            self.request("operator", "HUMAN", self.source("service-refusal.txt"), scope))
        self.assertIs(returned, terminal)
        self.assertEqual(returned["outcome"], "REFUSED")
        self.assertEqual(self.gateway_events("gateway-returned-receipt")[-1]["payload"]
                         ["terminal_outcome"], "REFUSED")


if __name__ == "__main__":
    unittest.main()
