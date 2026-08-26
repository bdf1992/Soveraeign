"""Every refusal code this service produces, against the manifest that declares them.

`scripts/sovkernel/manifests.py` checks that a *declared* refusal is a code the
kernel knows. Nothing checked the other direction, and the service walked through
that gap: `UNKNOWN_RECORD` came back from eight operations and appeared in
`services/console/contracts/service.json` nowhere at all, so a caller matching on
`reason_code` had no declared name for a refusal it could receive. The same fact
about the same thread in the same journal came back as `THREAD_UNKNOWN` through
`ConsoleRoutes` and `UNKNOWN_RECORD` through the CLI, so which name it had depended
on which surface asked.

Both are the same fact - the named record is not one this node's journal carries -
and both now carry `UNKNOWN_RECORD`, declared per operation.

The cases here are a pair. The positive drives each operation against an absent
identifier and reads the code it actually produces. The defeating half is that the
code is then looked up in the manifest: an operation that starts answering with
something it does not declare fails here, and so does a declaration that stops
matching what the operation returns.

Passing establishes `BUILT`. It witnesses nothing.
"""

from __future__ import annotations

from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import contextlib
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import ConsoleRoutes, ConsoleService, cli  # noqa: E402
from soveraeign_console_service.refusals import UnknownRecord  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import empty_journal  # noqa: E402

MANIFEST = json.loads(
    (ROOT / "services" / "console" / "contracts" / "service.json").read_text("utf-8"))
DECLARED = {entry["operation"]: set(entry["refusals"])
            for entry in MANIFEST["operations"]}
LOCAL = MANIFEST["local_refusals"]
NODE = "node:local"
BDO = "Bdo"
ABSENT_THREAD = "thread_0000000000000000"
ABSENT_SESSION = "session_0000000000000000"
ABSENT_CHANNEL = "channel_0000000000000000"
ABSENT_GRANT = "grant_0000000000000000"
ABSENT_PUBLICATION = "publication_0000000000000000"


class DeclaredVocabulary(unittest.TestCase):
    """What the manifest says, read on its own before anything is driven."""

    def test_the_retired_thread_code_is_gone_from_the_manifest(self) -> None:
        self.assertNotIn("THREAD_UNKNOWN", LOCAL)
        for operation, refusals in DECLARED.items():
            with self.subTest(operation=operation):
                self.assertNotIn("THREAD_UNKNOWN", refusals)

    def test_the_absent_record_code_maps_to_a_kernel_refusal(self) -> None:
        """A local code is a name for a kernel refusal, never a second vocabulary."""
        kernel = {code for row in json.loads(
            (ROOT / "contracts" / "kernel-transitions.json").read_text("utf-8"))
            ["transitions"] for code in row["refusals"]}
        self.assertIn(LOCAL[UnknownRecord.reason_code], kernel)
        self.assertEqual(LOCAL[UnknownRecord.reason_code], "MISSING_PRECONDITION")

    def test_the_operations_that_read_a_record_by_id_declare_it(self) -> None:
        for operation in sorted(ProducedRefusals.ABSENT_ID):
            with self.subTest(operation=operation):
                self.assertIn(UnknownRecord.reason_code, DECLARED[operation])


class ProducedRefusals(unittest.TestCase):
    """Every operation that reads a record by id, driven against an id nothing carries."""

    #: operation name -> the CLI arguments that name an absent record. The operator
    #: holds every grant the operation checks, so what refuses is the missing record
    #: and never the authority - which is the distinction the case is testing.
    ABSENT_ID: dict[str, list[str]] = {
        "archive-thread": ["archive-thread", "--operator", BDO, "--thread", ABSENT_THREAD],
        "close-session": ["close-session", "--operator", BDO, "--session", ABSENT_SESSION],
        "open-thread": ["open-thread", "--operator", BDO, "--channel", ABSENT_CHANNEL,
                        "--title", "nowhere"],
        "post": ["post", "--operator", BDO, "--session", ABSENT_SESSION,
                 "--thread", ABSENT_THREAD, "--body", "x"],
        "publish-thread": ["publish-thread", "--operator", BDO, "--thread", ABSENT_THREAD],
        "read-thread": ["read-thread", "--operator", BDO, "--thread", ABSENT_THREAD],
        "revoke": ["revoke", "--grant", ABSENT_GRANT, "--revoked-by", BDO],
        "withdraw-publication": ["withdraw-publication", "--operator", BDO,
                                 "--publication", ABSENT_PUBLICATION],
    }

    def setUp(self) -> None:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        self.store = Path(holder.name) / "console"
        self.store.mkdir(parents=True)
        record = RecordService(empty_journal(self.store / "journal"))
        console = ConsoleService(record, self.store, NODE)
        # Bdo opens this node's office and takes every grant the eight operations
        # check, over the exact absent subjects they will be pointed at.
        console.grant(BDO, "read:thread", ABSENT_THREAD, granted_by=BDO)
        for capability, scope in (("archive:thread", ABSENT_CHANNEL),
                                  ("close:session", BDO),
                                  ("open:thread", ABSENT_CHANNEL),
                                  ("post:message", ABSENT_THREAD),
                                  ("publish:thread", ABSENT_THREAD)):
            console.grant(BDO, capability, scope, granted_by=BDO)
        record.close()

    def run_cli(self, arguments: list[str]) -> tuple[int, dict[str, Any]]:
        out = StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["--root", str(self.store), "--node", NODE, *arguments])
        return code, json.loads(out.getvalue())

    def test_each_operation_answers_an_absent_id_with_a_declared_code(self) -> None:
        for operation, arguments in sorted(self.ABSENT_ID.items()):
            with self.subTest(operation=operation):
                code, answer = self.run_cli(arguments)
                self.assertEqual(answer["outcome"], "REFUSED")
                self.assertEqual(answer["reason_code"], UnknownRecord.reason_code,
                                 f"{operation} did not answer the absent-record fact")
                self.assertIn(answer["reason_code"], DECLARED[operation],
                              f"{operation} produced a code its manifest does not declare")
                self.assertEqual(code, 3)

    def test_the_answer_never_says_whose_record_it_would_have_been(self) -> None:
        """A foreign record is answered exactly as a missing one, message included."""
        record = RecordService(self.store / "journal")
        peer = ConsoleService(record, self.store, "node:peer")
        peer.grant("mallory", "open:channel", "work", granted_by="mallory")
        channel = peer.open_channel("mallory", "work", "work")
        peer.grant("mallory", "open:thread", channel["channel_id"], granted_by="mallory")
        thread = peer.open_thread("mallory", channel["channel_id"], "peer thread")
        record.close()
        _, foreign = self.run_cli(["archive-thread", "--operator", BDO,
                                   "--thread", thread["thread_id"]])
        _, missing = self.run_cli(["archive-thread", "--operator", BDO,
                                   "--thread", ABSENT_THREAD])
        self.assertEqual(foreign["reason_code"], missing["reason_code"])
        self.assertNotIn("node:peer", json.dumps(foreign))


class OnePathAgreesWithTheOther(unittest.TestCase):
    """The routed read and the CLI read, asked the same question about one journal."""

    def setUp(self) -> None:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        self.store = Path(holder.name) / "console"
        self.store.mkdir(parents=True)
        self.record = RecordService(empty_journal(self.store / "journal"))
        self.addCleanup(self.record.close)
        self.console = ConsoleService(self.record, self.store, NODE)
        self.console.grant("reader", "open:session", "reader", granted_by=BDO)
        self.session = self.console.open_session("reader", "HUMAN", "human-binding")
        self.console.grant("reader", "read:thread", ABSENT_THREAD, granted_by=BDO)
        self.routes = ConsoleRoutes(self.console)

    def cli_reason(self) -> str:
        out = StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["--root", str(self.store), "--node", NODE, "read-thread",
                      "--operator", "reader", "--thread", ABSENT_THREAD])
        return json.loads(out.getvalue())["reason_code"]

    def route_reason(self) -> str:
        receipt = self.routes.call("read-thread", {
            "thread_id": ABSENT_THREAD,
            "session_id": self.session["session_id"]}, "reader")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        return receipt["payload"]["detail"]["reason_code"]

    def test_both_paths_name_the_absent_thread_the_same_way(self) -> None:
        self.assertEqual(self.route_reason(), self.cli_reason())
        self.assertEqual(self.route_reason(), UnknownRecord.reason_code)

    def test_the_shared_code_is_declared_for_the_operation(self) -> None:
        self.assertIn(self.route_reason(), DECLARED["read-thread"])


class RaisedTypesCarryTheCode(unittest.TestCase):
    """The read helpers and the CLI name one constant rather than spelling a string."""

    def test_the_absent_record_error_carries_its_reason_code(self) -> None:
        self.assertEqual(UnknownRecord.reason_code, "UNKNOWN_RECORD")

    def test_the_direct_read_raises_the_typed_error(self) -> None:
        """`continuity.read_thread` raised a bare KeyError, which carries no code."""
        from soveraeign_console_service.continuity import read_thread

        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        store = Path(holder.name) / "console"
        store.mkdir(parents=True)
        record = RecordService(empty_journal(store / "journal"))
        self.addCleanup(record.close)
        console = ConsoleService(record, store, NODE)
        console.grant("reader", "read:thread", ABSENT_THREAD, granted_by=BDO)
        with self.assertRaises(UnknownRecord):
            read_thread(console, ABSENT_THREAD, "human-binding", operator_id="reader")


if __name__ == "__main__":
    unittest.main()
