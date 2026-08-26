from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
for service in ("console", "gateway", "host", "record"):
    sys.path.insert(0, str(ROOT / "services" / service / "src"))
sys.path.insert(0, str(ROOT / "adapters" / "host"))

from local_host_adapter import ADAPTER_ID, LocalHostAdapter  # noqa: E402
from soveraeign_console_service import ConsoleService  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
from soveraeign_gateway_service import Gateway, load_surface  # noqa: E402
from soveraeign_host_service import (  # noqa: E402
    HostAdapterUnavailable,
    HostRoutes,
    HostService,
    snapshot_defect,
)
from soveraeign_record_service import RecordService  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402


SNAPSHOT = {
    "schema_version": "soveraeign-host-health/v1",
    "adapter_id": "urn:soveraeign:adapter:test-host:v1",
    "captured_at": "2026-08-25T12:00:00+00:00",
    "boundary": "PROCESS_EXECUTION_HOST",
    "platform": {"system": "TestOS", "release": "1", "machine": "test64"},
    "processor": {"logical_count": 4, "load_average": [0.1, 0.2, 0.3]},
    "memory": {"total_bytes": 8192, "available_bytes": 4096},
    "uptime_seconds": 3600.0,
    "boot_id": "boot-test-1",
    "limitations": ["adapter_reading_is_not_independent_observation"],
}
SENSITIVE_DIAGNOSTIC = "credential=s3cr3t-token /private/host/path"


class FixedAdapter:
    adapter_id = SNAPSHOT["adapter_id"]

    def __init__(self) -> None:
        self.calls = 0

    def read_health(self) -> dict[str, Any]:
        self.calls += 1
        return deepcopy(SNAPSHOT)


class UnavailableAdapter(FixedAdapter):
    def read_health(self) -> dict[str, Any]:
        self.calls += 1
        raise HostAdapterUnavailable(SENSITIVE_DIAGNOSTIC)


class BrokenAdapter(FixedAdapter):
    def read_health(self) -> dict[str, Any]:
        self.calls += 1
        raise RuntimeError(SENSITIVE_DIAGNOSTIC)


class HostServiceReading(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.record = RecordService(Path(self.tmp.name) / "record")
        self.adapter = FixedAdapter()
        self.service = HostService(self.record, self.adapter)

    def tearDown(self) -> None:
        self.record.close()
        self.tmp.cleanup()

    def detail(self, receipt: dict[str, Any]) -> dict[str, Any]:
        return receipt["payload"]["detail"]

    def test_health_read_is_a_durable_service_owned_terminal_receipt(self) -> None:
        receipt = self.service.read_health("operator")

        self.assertEqual(receipt, self.record.entry(receipt["entry_id"]))
        self.assertEqual(receipt["kind"], "RECEIPT")
        self.assertEqual(receipt["actor"], "operator")
        self.assertEqual(receipt["payload"]["outcome"], "COMMITTED")
        self.assertEqual(receipt["payload"]["event"], "host.read-health")
        self.assertEqual(self.detail(receipt)["host_id"], "host:local")
        self.assertEqual(self.detail(receipt)["snapshot"], SNAPSHOT)
        self.assertEqual(
            self.detail(receipt)["observation_status"],
            "UNATTESTED_ADAPTER_READING",
        )

    def test_adapter_unavailable_is_a_refusal_not_fabricated_health(self) -> None:
        service = HostService(self.record, UnavailableAdapter())
        receipt = service.read_health("operator")
        serialized = json.dumps(receipt, sort_keys=True)

        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(receipt)["reason_code"], "HOST_UNAVAILABLE")
        self.assertNotIn("snapshot", self.detail(receipt))
        self.assertNotIn("diagnostic", self.detail(receipt))
        self.assertNotIn("s3cr3t-token", serialized)
        self.assertNotIn("/private/host/path", serialized)

    def test_unexpected_adapter_fault_is_a_failed_host_receipt(self) -> None:
        service = HostService(self.record, BrokenAdapter())
        receipt = service.read_health("operator")
        serialized = json.dumps(receipt, sort_keys=True)

        self.assertEqual(receipt["payload"]["outcome"], "FAILED")
        self.assertEqual(self.detail(receipt)["reason_code"], "HOST_READ_FAILED")
        self.assertEqual(self.detail(receipt)["error_type"], "RuntimeError")
        self.assertNotIn("diagnostic", self.detail(receipt))
        self.assertNotIn("s3cr3t-token", serialized)
        self.assertNotIn("/private/host/path", serialized)

    def test_adapter_cannot_change_boundary_or_smuggle_extra_fields(self) -> None:
        for label, mutate, reason in (
            ("boundary", lambda item: item.__setitem__("boundary", "PHYSICAL_MACHINE"),
             "HOST_BOUNDARY_UNKNOWN"),
            ("adapter", lambda item: item.__setitem__("adapter_id", "foreign"),
             "HOST_BOUNDARY_UNKNOWN"),
            ("hostname", lambda item: item.__setitem__("hostname", "secret-host"),
             "HOST_READ_FAILED"),
        ):
            with self.subTest(label=label):
                snapshot = deepcopy(SNAPSHOT)
                mutate(snapshot)

                class ChangedAdapter(FixedAdapter):
                    def read_health(self) -> dict[str, Any]:
                        return snapshot

                receipt = HostService(self.record, ChangedAdapter()).read_health("operator")
                self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
                self.assertEqual(self.detail(receipt)["reason_code"], reason)
                self.assertNotIn("snapshot", self.detail(receipt))

    def test_route_has_no_domain_arguments_and_returns_terminal_refusal(self) -> None:
        routes = HostRoutes(self.service)
        self.assertEqual(routes.operation_ids(), ("read-health",))
        self.assertEqual(routes.argument_contract("read-health"), {
            "required": (), "optional": (),
        })
        receipt = routes.call("read-health", {"hostname": "not-an-input"}, "operator")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(receipt)["reason_code"], "MALFORMED_HOST_REQUEST")
        self.assertEqual(self.adapter.calls, 0)

    def test_local_adapter_matches_contract_without_disclosing_hostname(self) -> None:
        snapshot = LocalHostAdapter().read_health()
        schema = json.loads(
            (ROOT / "services" / "host" / "contracts" /
             "host-health.schema.json").read_text("utf-8"))
        self.assertEqual(validate(snapshot, schema), [])
        self.assertIsNone(snapshot_defect(snapshot, ADAPTER_ID))
        self.assertEqual(snapshot["boundary"], "PROCESS_EXECUTION_HOST")
        self.assertNotIn("hostname", snapshot)


class HostGatewayVertical(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.record = RecordService(root / "record")
        self.console = ConsoleService(self.record, root / "console", "node:test")
        self.adapter = FixedAdapter()
        self.host = HostService(self.record, self.adapter)
        capability_map, manifests, table = load_surface(ROOT)

        def authority(actor: str, capability: str, scope: str) -> str:
            return console_authority.check(
                self.record.reconstruct(), self.console.node_id, actor, capability,
                scope)

        self.gateway = Gateway(
            self.record, capability_map, manifests, table, authority,
            {"host:in-process": HostRoutes(self.host).call},
            authority_denials=(AuthorityRefused,),
        )

    def tearDown(self) -> None:
        self.record.close()
        self.tmp.cleanup()

    def request(self, actor: str, actor_kind: str = "HUMAN",
                arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return {
            "actor": actor,
            "actor_kind": actor_kind,
            "logical_endpoint": "sov://host/read-health",
            "transport": "IN_PROCESS",
            "scope": "host:local",
            "arguments": arguments or {},
        }

    def detail(self, receipt: dict[str, Any]) -> dict[str, Any]:
        return receipt["payload"]["detail"]

    def test_human_and_model_use_same_route_and_service_receipt(self) -> None:
        for actor, actor_kind in (("operator", "HUMAN"), ("local-model", "MODEL")):
            with self.subTest(actor_kind=actor_kind):
                self.console.grant(actor, "read:host-health", "host:local")
                returned = self.gateway.dispatch(self.request(actor, actor_kind))
                self.assertEqual(returned, self.record.entry(returned["entry_id"]))
                self.assertEqual(returned["payload"]["outcome"], "COMMITTED")
                self.assertEqual(returned["payload"]["event"], "host.read-health")
                self.assertEqual(returned["actor"], actor)
        self.assertEqual(self.adapter.calls, 2)

    def test_missing_grant_refuses_before_the_adapter(self) -> None:
        returned = self.gateway.dispatch(self.request("mallory", "MODEL"))
        self.assertEqual(returned["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(returned)["reason_code"], "AUTHORITY_REFUSED")
        self.assertEqual(self.adapter.calls, 0)

    def test_client_attribution_override_refuses_before_the_adapter(self) -> None:
        self.console.grant("operator", "read:host-health", "host:local")
        returned = self.gateway.dispatch(
            self.request("operator", arguments={"actor": "mallory"}))
        self.assertEqual(returned["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(returned)["reason_code"], "MALFORMED_REQUEST")
        self.assertEqual(self.adapter.calls, 0)

    def test_service_argument_refusal_crosses_gateway_unchanged(self) -> None:
        self.console.grant("operator", "read:host-health", "host:local")
        returned = self.gateway.dispatch(
            self.request("operator", arguments={"physical_host": True}))
        self.assertEqual(returned["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(returned)["reason_code"], "MALFORMED_HOST_REQUEST")
        self.assertEqual(self.adapter.calls, 0)

    def test_declared_restart_is_not_policy_active_or_routed(self) -> None:
        request = self.request("operator")
        request["logical_endpoint"] = "sov://host/restart"
        returned = self.gateway.dispatch(request)
        self.assertEqual(returned["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(returned)["reason_code"], "TRANSPORT_NOT_ACTIVATED")
        self.assertEqual(self.adapter.calls, 0)


if __name__ == "__main__":
    unittest.main()
