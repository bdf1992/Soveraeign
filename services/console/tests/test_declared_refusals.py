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

    def receipts(self) -> list[dict[str, Any]]:
        """Every REFUSED receipt in the store's journal, read back independently."""
        record = RecordService(self.store / "journal")
        try:
            return [entry for entry in record.reconstruct()
                    if entry["kind"] == "RECEIPT"
                    and entry["payload"].get("outcome") == "REFUSED"]
        finally:
            record.close()

    def test_each_absent_record_refusal_is_written_down(self) -> None:
        """`append.py`: a refusal leaving no trace is not distinguishable from no attempt.

        Declaring `UNKNOWN_RECORD` put it under that rule. It was raised out of the read
        helpers, which hold no journal handle, so the one code the manifest had just
        named was the one that left nothing behind - while `ConsoleRoutes` recorded it.
        """
        for operation, arguments in sorted(self.ABSENT_ID.items()):
            with self.subTest(operation=operation):
                before = len(self.receipts())
                self.run_cli(arguments)
                written = self.receipts()[before:]
                codes = [entry["payload"]["detail"]["reason_code"] for entry in written]
                self.assertIn(UnknownRecord.reason_code, codes,
                              f"{operation} refused and left no receipt saying so")
                events = {entry["payload"]["event"] for entry in written}
                self.assertIn(f"console.{operation}", events)

    def test_a_foreign_record_reads_as_missing_where_no_grant_was_shown_yet(self) -> None:
        """The collapse holds for the reads that run before the caller shows anything."""
        _, thread_id = self.peer_records()
        _, foreign = self.run_cli(["archive-thread", "--operator", BDO,
                                   "--thread", thread_id])
        _, missing = self.run_cli(["archive-thread", "--operator", BDO,
                                   "--thread", ABSENT_THREAD])
        self.assertEqual(foreign["reason_code"], missing["reason_code"])
        self.assertEqual(foreign["reason_code"], UnknownRecord.reason_code)
        self.assertNotIn("node:peer", json.dumps(foreign))

    def test_a_caller_that_showed_a_grant_first_is_told_the_record_is_elsewhere(self):
        """And it is told so in a declared code, which is what the manifest must carry.

        `open-thread`, `post` and `publish-thread` check authority before reading,
        because the grant's scope is an id the caller supplied. `core.owned` holds that
        a caller which has shown a grant over the subject has earned being told the
        record belongs to another node, so those do not collapse to the missing answer.
        Both codes are declared for them, which is the whole requirement: the answer may
        differ, the vocabulary may not be undeclared.
        """
        channel_id, thread_id = self.peer_records()
        cases = (("publish-thread", ["publish-thread", "--operator", BDO,
                                     "--thread", thread_id]),
                 ("open-thread", ["open-thread", "--operator", BDO,
                                  "--channel", channel_id, "--title", "elsewhere"]))
        for operation, arguments in cases:
            with self.subTest(operation=operation):
                _, foreign = self.run_cli(arguments)
                self.assertEqual(foreign["reason_code"], "FOREIGN_NODE_RECORD")
                self.assertIn("FOREIGN_NODE_RECORD", DECLARED[operation])
                self.assertIn(UnknownRecord.reason_code, DECLARED[operation])

    def peer_records(self) -> tuple[str, str]:
        """A channel and thread another node opened on this journal, reachable by Bdo.

        Bdo is granted over the peer's exact ids, so what refuses is the record's node
        and never the authority - which is the distinction the case is testing.
        """
        record = RecordService(self.store / "journal")
        peer = ConsoleService(record, self.store, "node:peer")
        peer.grant("mallory", "open:channel", "work", granted_by="mallory")
        channel = peer.open_channel("mallory", "work", "work")
        peer.grant("mallory", "open:thread", channel["channel_id"], granted_by="mallory")
        thread = peer.open_thread("mallory", channel["channel_id"], "peer thread")
        local = ConsoleService(record, self.store, NODE)
        local.grant(BDO, "publish:thread", thread["thread_id"], granted_by=BDO)
        local.grant(BDO, "open:thread", channel["channel_id"], granted_by=BDO)
        record.close()
        return str(channel["channel_id"]), str(thread["thread_id"])


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


class AnUnreadableProjectionIsNotAMissingRecord(unittest.TestCase):
    """`console.discover-operations` read the capability map's keys on faith.

    A map that is valid JSON and the wrong shape raised `KeyError`, and the CLI's
    catch-all labelled every `KeyError` `UNKNOWN_RECORD` - a code this operation does
    not declare, and the wrong thing to say besides, since nothing was missing from the
    journal. A file that was absent or unparseable did worse: a traceback on stderr,
    nothing on stdout, against this CLI's own promise that every answer is one JSON
    object. `UNREADABLE` is the kernel's code for a source that cannot be read.
    """

    def setUp(self) -> None:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        self.tmp = Path(holder.name)
        self.store = self.tmp / "console"
        self.store.mkdir(parents=True)
        record = RecordService(empty_journal(self.store / "journal"))
        console = ConsoleService(record, self.store, NODE)
        console.grant(BDO, "read:session", BDO, granted_by=BDO)
        record.close()
        self.good = json.loads((ROOT / "contracts" / "fixtures"
                                / "capability-map.reference.json").read_text("utf-8"))

    def ask(self, map_path: Path) -> tuple[int, dict[str, Any]]:
        out = StringIO()
        with contextlib.redirect_stdout(out):
            code = cli.main(["--root", str(self.store), "--node", NODE, "operations",
                             "--operator", BDO, "--capability-map", str(map_path)])
        return code, json.loads(out.getvalue())

    def write(self, name: str, content: str) -> Path:
        path = self.tmp / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_the_reference_map_still_answers(self) -> None:
        """The positive half: nothing here refuses a projection that is readable."""
        path = self.write("good.json", json.dumps(self.good))
        code, answer = self.ask(path)
        self.assertEqual(code, 0)
        self.assertEqual(answer["counts"]["declared"], len(self.good["capabilities"]))

    def test_a_map_short_a_key_refuses_with_a_declared_code(self) -> None:
        broken = dict(self.good)
        broken.pop("capabilities")
        code, answer = self.ask(self.write("no-capabilities.json", json.dumps(broken)))
        self.assertEqual(answer["reason_code"], "UNREADABLE")
        self.assertIn("UNREADABLE", DECLARED["discover-operations"])
        self.assertEqual(code, 2)

    def test_a_row_short_a_key_refuses_the_same_way(self) -> None:
        broken = dict(self.good)
        rows = [dict(row) for row in broken["capabilities"]]
        rows[0].pop("required_authority")
        broken["capabilities"] = rows
        code, answer = self.ask(self.write("no-authority.json", json.dumps(broken)))
        self.assertEqual(answer["reason_code"], "UNREADABLE")
        self.assertIn("required_authority", answer["message"])
        self.assertEqual(code, 2)

    def test_a_missing_or_unparseable_file_still_answers_in_json(self) -> None:
        for name, path in (("absent", self.tmp / "not-here.json"),
                           ("not JSON", self.write("bad.json", "{not json"))):
            with self.subTest(name):
                code, answer = self.ask(path)
                self.assertEqual(answer["outcome"], "REFUSED")
                self.assertEqual(answer["reason_code"], "UNREADABLE")
                self.assertEqual(code, 2)


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
