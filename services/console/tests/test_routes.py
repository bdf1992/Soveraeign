"""Service-owned Console read route and Node object record tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from hashlib import sha256
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import ConsoleRoutes, ConsoleService  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402
from sovkernel.jsonschema import validate  # noqa: E402


class ConsoleReadRoute(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        root = Path(self.tmp.name)
        self.record = RecordService(root / "record")
        self.console = ConsoleService(self.record, root / "console", "node:test")
        self.console.grant("reader", "open:channel", "work")
        channel = self.console.open_channel("reader", "work", "work")
        self.console.grant("reader", "open:thread", channel["channel_id"])
        self.thread = self.console.open_thread(
            "reader", channel["channel_id"], "Read plane")
        self.session = self.console.open_session("reader", "HUMAN", "human-binding")
        self.console.grant("reader", "post:message", self.thread["thread_id"])
        self.post = self.console.post(
            self.session["session_id"], self.thread["thread_id"], b"grounded post")
        self.routes = ConsoleRoutes(self.console)

    def tearDown(self) -> None:
        self.record.close()
        self.tmp.cleanup()

    def arguments(self, **updates: str) -> dict[str, str]:
        values = {
            "thread_id": self.thread["thread_id"],
            "session_id": self.session["session_id"],
        }
        values.update(updates)
        return values

    def detail(self, receipt: dict) -> dict:
        return receipt["payload"]["detail"]

    def reason(self, receipt: dict) -> str | None:
        return self.detail(receipt).get("reason_code")

    def test_read_returns_a_source_addressed_node_object_record(self) -> None:
        receipt = self.routes.call("read-thread", self.arguments(), "reader")
        self.assertEqual(receipt["payload"]["outcome"], "COMMITTED")
        self.assertEqual(receipt["payload"]["event"], "console.read-thread")
        self.assertEqual(receipt["actor"], "reader")
        detail = self.detail(receipt)
        self.assertEqual(detail["commit_semantics"], "DERIVED")
        self.assertEqual(detail["standing_effect"], "NONE")
        object_record = detail["object_record"]
        schema = json.loads(
            (ROOT / "contracts" / "node-object-record.schema.json").read_text("utf-8"))
        self.assertEqual(validate(object_record, schema), [])
        self.assertEqual(object_record["object_id"], self.thread["thread_id"])
        self.assertEqual(object_record["object_kind"], "thread")
        self.assertFalse(object_record["source"]["projection_authoritative"])
        self.assertEqual(object_record["data"]["read_through"], "human-binding")
        self.assertEqual(object_record["relations"][0], {
            "relation": "channel", "target_id": self.thread["channel_id"],
        })
        self.assertEqual(object_record["relations"][1]["target_digest"],
                         self.post["content_digest"])

    def test_unknown_and_malformed_object_identities_refuse_terminally(self) -> None:
        unknown = self.routes.call(
            "read-thread", self.arguments(thread_id="thread_0000000000000000"), "reader")
        malformed = self.routes.call(
            "read-thread", self.arguments(thread_id="not-a-thread"), "reader")
        self.assertEqual(unknown["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.reason(unknown), "THREAD_UNKNOWN")
        self.assertEqual(malformed["payload"]["outcome"], "REFUSED")
        self.assertEqual(self.reason(malformed), "MALFORMED_IDENTITY")

    def test_session_must_be_live_and_belong_to_the_checked_actor(self) -> None:
        other = self.console.open_session("other", "MODEL", "model-binding")
        mismatch = self.routes.call(
            "read-thread", self.arguments(session_id=other["session_id"]), "reader")
        self.assertEqual(self.reason(mismatch), "ACTOR_ATTRIBUTION_MISMATCH")
        self.console.close_session(self.session["session_id"])
        closed = self.routes.call("read-thread", self.arguments(), "reader")
        self.assertEqual(self.reason(closed), "SESSION_NOT_LIVE")

    def test_read_preserves_sources_and_changes_no_thread_or_post_record(self) -> None:
        before = self.record.reconstruct()
        receipt = self.routes.call("read-thread", self.arguments(), "reader")
        after = self.record.reconstruct()
        object_record = self.detail(receipt)["object_record"]
        self.assertEqual(after[:-1], before)
        self.assertEqual(after[-1], receipt)
        durable = {entry["entry_id"]: entry for entry in before}
        for source in object_record["source"]["records"]:
            self.assertEqual(durable[source["address"]]["entry_digest"], source["digest"])
        for receipt_ref in object_record["receipt_refs"]:
            self.assertEqual(durable[receipt_ref]["kind"], "RECEIPT")
        revision = object_record["revision"]
        expected_revision = sha256(json.dumps(
            object_record["source"]["records"], sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()
        self.assertEqual(revision, {
            "address": f"urn:sha256:{expected_revision}", "digest": expected_revision,
        })
        self.assertEqual(object_record["source"]["snapshot_digest"], before[-1]["entry_digest"])

    def test_revision_changes_with_thread_content_not_with_read_receipts(self) -> None:
        first = self.detail(
            self.routes.call("read-thread", self.arguments(), "reader"))["object_record"]
        second = self.detail(
            self.routes.call("read-thread", self.arguments(), "reader"))["object_record"]
        self.assertEqual(first["revision"], second["revision"])
        self.console.post(
            self.session["session_id"], self.thread["thread_id"], b"second post")
        changed = self.detail(
            self.routes.call("read-thread", self.arguments(), "reader"))["object_record"]
        self.assertNotEqual(first["revision"], changed["revision"])

    def test_route_census_and_argument_identity_are_service_owned(self) -> None:
        self.assertEqual(ConsoleRoutes.operation_ids(), ("read-thread",))
        self.assertEqual(ConsoleRoutes.argument_contract("read-thread"), {
            "required": ("thread_id", "session_id"), "optional": (),
        })
        with self.assertRaises(KeyError):
            self.routes.call("read-session", self.arguments(), "reader")
        refused = self.routes.call(
            "read-thread", {**self.arguments(), "actor": "spoof"}, "reader")
        self.assertEqual(self.reason(refused), "MALFORMED_IDENTITY")


if __name__ == "__main__":
    unittest.main()
