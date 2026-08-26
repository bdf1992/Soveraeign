"""Node/Gateway proof for the existing Console thread object read."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
for service in ("gateway", "console", "record"):
    sys.path.insert(0, str(ROOT / "services" / service / "src"))

from soveraeign_console_service import ConsoleRoutes  # noqa: E402
from soveraeign_console_service import authority as console_authority  # noqa: E402
from soveraeign_console_service.refusals import AuthorityRefused  # noqa: E402
from soveraeign_gateway_service import Gateway, load_surface  # noqa: E402
from sovnode.bindings import HUMAN, MODEL, invocation_request, resolve  # noqa: E402
from sovnode.composition import LocalActionPath, route_census  # noqa: E402
from sovnode.interface_inputs import rebuild  # noqa: E402


class ConsoleHorizontal(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.node = LocalActionPath(Path(self.tmp.name) / "node")
        self.document, defects = rebuild()
        if defects:
            raise RuntimeError(defects)
        self.operation = resolve(self.document, "console.read-thread")
        # Use the exact authority capabilities declared by current main. These are
        # setup grants for the object we read; they do not grant the read itself.
        self.node.console.grant("reader", "open:channel", "work", "Bdo")
        channel = self.node.console.open_channel("reader", "work", "work")
        self.node.console.grant("reader", "open:thread", channel["channel_id"], "Bdo")
        self.thread = self.node.console.open_thread(
            "reader", channel["channel_id"], "Horizontal read")
        self.node.console.grant("reader", "post:message", self.thread["thread_id"], "Bdo")
        self.node.console.grant("reader", "open:session", "reader", "Bdo")
        self.sessions = {
            HUMAN: self.node.console.open_session("reader", HUMAN, "human-binding"),
            MODEL: self.node.console.open_session("reader", MODEL, "model-binding"),
        }
        self.node.console.post(
            "reader", self.sessions[HUMAN]["session_id"], self.thread["thread_id"], b"one object")

    def tearDown(self) -> None:
        self.node.close()
        self.tmp.cleanup()

    def request(self, binding: str, *, actor: str = "reader",
                thread_id: str | None = None) -> dict:
        thread_id = thread_id or self.thread["thread_id"]
        return invocation_request(
            self.document, "console.read-thread", binding, actor, thread_id,
            {"thread_id": thread_id, "session_id": self.sessions[binding]["session_id"]},
        )

    @staticmethod
    def detail(receipt: dict) -> dict:
        return receipt["payload"]["detail"]

    def test_human_and_model_read_the_same_persisted_thread_through_node(self) -> None:
        self.node.console.grant("reader", "read:thread", self.thread["thread_id"], "Bdo")
        results = {}
        for binding in (HUMAN, MODEL):
            returned = self.node.dispatch(self.request(binding))
            self.assertEqual(returned["payload"]["outcome"], "COMMITTED")
            self.assertEqual(returned["payload"]["event"], "console.read-thread")
            self.assertEqual(returned, self.node.record.entry(returned["entry_id"]))
            results[binding] = self.detail(returned)["object_record"]
        self.assertEqual(results[HUMAN]["object_id"], results[MODEL]["object_id"])
        self.assertEqual(results[HUMAN]["revision"], results[MODEL]["revision"])
        self.assertEqual(results[HUMAN]["data"]["posts"], results[MODEL]["data"]["posts"])
        self.assertEqual(results[HUMAN]["data"]["read_through"], "human-binding")
        self.assertEqual(results[MODEL]["data"]["read_through"], "model-binding")

    def test_authority_and_actor_policy_refuse_before_console_route(self) -> None:
        ungranted = self.node.dispatch(self.request(HUMAN))
        self.assertEqual(self.detail(ungranted)["reason_code"], "AUTHORITY_REFUSED")
        self.assertFalse(any(
            entry["payload"].get("event") == "console.read-thread"
            for entry in self.node.record.entries() if entry["kind"] == "RECEIPT"))

        request = self.request(HUMAN)
        request["actor_kind"] = "SYSTEM"
        policy_refusal = self.node.dispatch(request)
        self.assertEqual(self.detail(policy_refusal)["reason_code"], "AUTHORITY_REFUSED")
        self.assertEqual(self.detail(policy_refusal)["diagnostic_code"],
                         "ACTOR_KIND_NOT_ADMITTED")

    def test_unknown_object_refusal_survives_gateway_unchanged(self) -> None:
        unknown = "thread_0000000000000000"
        self.node.console.grant("reader", "read:thread", unknown, "Bdo")
        returned = self.node.dispatch(self.request(HUMAN, thread_id=unknown))
        self.assertEqual(returned["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.detail(returned)["reason_code"], "THREAD_UNKNOWN")
        self.assertEqual(returned, self.node.record.entry(returned["entry_id"]))

    def test_route_projection_drift_fails_before_console_execution(self) -> None:
        self.node.console.grant("reader", "read:thread", self.thread["thread_id"], "Bdo")
        capability_map, manifests, table = load_surface(ROOT)
        tampered = deepcopy(capability_map)
        row = next(item for item in tampered["capabilities"]
                   if item["capability_id"] == "console.read-thread")
        endpoint = next(item for item in row["endpoints"]
                        if item["transport"] == "IN_PROCESS")
        endpoint["address"] = "console:drifted"

        def authority(actor: str, capability: str, scope: str) -> str:
            return console_authority.check(
                self.node.record.reconstruct(), self.node.node_id, actor, capability,
                scope)

        gateway = Gateway(
            self.node.record, tampered, manifests, table, authority,
            {"console:in-process": ConsoleRoutes(self.node.console).call},
            authority_denials=(AuthorityRefused,),
        )
        before = len([entry for entry in self.node.record.entries()
                      if entry["kind"] == "RECEIPT"
                      and entry["payload"].get("event") == "console.read-thread"])
        failed = gateway.dispatch(self.request(HUMAN))
        self.assertEqual(failed["payload"]["outcome"], "FAILED")
        self.assertEqual(self.detail(failed)["reason_code"], "CAPABILITY_MAP_INVALID")
        after = len([entry for entry in self.node.record.entries()
                     if entry["kind"] == "RECEIPT"
                     and entry["payload"].get("event") == "console.read-thread"])
        self.assertEqual(after, before)

    def test_node_interface_sources_and_route_arguments_are_exact(self) -> None:
        self.assertTrue(self.operation["facts"]["reachable"])
        route = self.operation["reachability"][0]
        self.assertEqual(route["required_arguments"], ["thread_id", "session_id"])
        self.assertEqual(route["address"], "console:in-process")
        self.assertIn("services/console/src/soveraeign_console_service/routes.py",
                      route["source_addresses"])
        census = next(item for item in route_census()
                      if item["operation_id"] == "console.read-thread")
        self.assertEqual(census["source_addresses"], route["source_addresses"])


if __name__ == "__main__":
    unittest.main()
