"""Defeating cases for the durable-principal / isolated-session join.

A Console session is a continuity boundary, not a bearer token. Knowing a valid
session id must not let a caller write as another operator or retrofit a different
durable principal onto an already-open session. Principal provenance grants no
authority; the ordinary operator/grant check still runs first.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parents[2] / "record" / "src"))

from soveraeign_console_service import ConsoleService, contract  # noqa: E402
from soveraeign_console_service.refusals import ActorAttributionMismatch  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

NODE = "node:test"


class PrincipalSessionIsolation(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.tmp.name) / "console"
        self.record = RecordService(root / "journal")
        self.console = ConsoleService(self.record, root, NODE)

        self.console.grant("Bdo", "open:channel", "work", "Bdo")
        channel = self.console.open_channel("Bdo", "work", "work")
        self.console.grant("Bdo", "open:thread", channel["channel_id"], "Bdo")
        thread = self.console.open_thread("Bdo", channel["channel_id"], "identity boundary")
        self.thread_id = thread["thread_id"]

        self.console.grant("sov", "open:session", "sov", "Bdo")
        self.console.grant("sov", "post:message", self.thread_id, "Bdo")

    def tearDown(self) -> None:
        self.record.close()
        self.tmp.cleanup()

    def test_a_known_principal_is_pinned_to_the_session(self) -> None:
        session = self.console.open_session(
            "sov", "MODEL", "model-binding", "principal:sov")

        with self.assertRaises(ActorAttributionMismatch) as refused:
            self.console.post(
                "sov", session["session_id"], self.thread_id, b"wrong principal",
                principal_id="principal:someone-else")

        self.assertEqual(refused.exception.reason_code, "ACTOR_ATTRIBUTION_MISMATCH")
        records = contract.records(self.record.reconstruct())
        self.assertEqual(records["posts"], [])
        receipt = self.record.reconstruct()[-1]
        self.assertEqual(receipt["kind"], "RECEIPT")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(
            receipt["payload"]["detail"]["reason_code"],
            "ACTOR_ATTRIBUTION_MISMATCH")

    def test_an_unresolved_session_does_not_infer_a_principal(self) -> None:
        session = self.console.open_session("sov", "MODEL", "model-binding")
        self.console.post("sov", session["session_id"], self.thread_id, b"no identity guess")

        records = contract.records(self.record.reconstruct())
        self.assertIsNone(records["operator_sessions"][0]["principal_id"])
        self.assertIsNone(records["posts"][0]["principal_id"])

    def test_matching_principal_is_recorded_as_provenance_not_authority(self) -> None:
        session = self.console.open_session(
            "sov", "MODEL", "model-binding", "principal:sov")
        self.console.post(
            "sov", session["session_id"], self.thread_id, b"same principal",
            principal_id="principal:sov")

        post = contract.records(self.record.reconstruct())["posts"][0]
        self.assertEqual(post["principal_id"], "principal:sov")
        self.assertEqual(post["session_id"], session["session_id"])
        self.assertEqual(post["binding_id"], "model-binding")


if __name__ == "__main__":
    unittest.main()
