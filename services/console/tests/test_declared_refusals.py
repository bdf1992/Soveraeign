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

from soveraeign_console_service import ConsoleRoutes, ConsoleService, authority, cli  # noqa: E402
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
#: The BUILT operations that name no record by id and therefore cannot answer
#: `UNKNOWN_RECORD`. Declared beside `ProducedRefusals.ABSENT_ID` so the two together
#: have to account for every BUILT operation the manifest carries.
NO_RECORD_BY_ID = {"discover-operations", "grant", "list-grants", "list-publications",
                   "open-channel", "open-session", "session-context"}


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

    def test_every_built_operation_is_accounted_for_by_name(self) -> None:
        """The table below is a declaration, so it is measured against the manifest.

        `ABSENT_ID` and `NO_RECORD_BY_ID` are hand-kept, and a case that walked only
        `ABSENT_ID` would grade the table against itself: a sixteenth BUILT operation
        nobody added would be invisible to every case in this module. An independent
        observation named that on 2026-08-26. The manifest is the source of the list,
        so adding an operation there and nowhere else fails here.
        """
        built = {entry["operation"] for entry in MANIFEST["operations"]
                 if entry["standing"] == "BUILT"}
        named = set(ProducedRefusals.ABSENT_ID) | NO_RECORD_BY_ID
        self.assertEqual(named, built,
                         "the manifest and this module's tables disagree on what is BUILT")
        self.assertFalse(set(ProducedRefusals.ABSENT_ID) & NO_RECORD_BY_ID)
        for operation in sorted(NO_RECORD_BY_ID):
            with self.subTest(operation=operation):
                self.assertNotIn(UnknownRecord.reason_code, DECLARED[operation],
                                 f"{operation} declares a code it cannot produce")


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

    def test_the_journal_does_not_restore_what_the_answer_collapsed(self) -> None:
        """The receipts have to match too, not only the two answers.

        Collapsing the answer and leaving one of the two silent moves the disclosure
        into the record instead of closing it: a reader of the journal - or anyone who
        can count entries - tells a foreign record from a missing one again. Dropping
        the refusal from `core.held_record` passes every other case in this suite.
        """
        _, thread_id = self.peer_records()
        for operation, subject in (("archive-thread", thread_id),
                                   ("archive-thread", ABSENT_THREAD)):
            before = len(self.receipts())
            self.run_cli([operation, "--operator", BDO, "--thread", subject])
            written = self.receipts()[before:]
            self.assertEqual(len(written), 1, f"{subject} wrote {len(written)} receipts")
            detail = written[0]["payload"]["detail"]
            self.assertEqual(detail["reason_code"], UnknownRecord.reason_code)
            self.assertEqual(written[0]["subject"], subject)
            self.assertEqual(written[0]["payload"]["event"], f"console.{operation}")
            # Everything except the id the caller itself supplied must be identical.
            self.assertEqual(
                {key: value for key, value in detail.items() if key != "message"},
                {"reason_code": UnknownRecord.reason_code,
                 "effect_class": "RECORD_LOCAL"})

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
                           ("not JSON", self.write("bad.json", "{not json")),
                           ("a directory", self.tmp)):
            with self.subTest(name):
                code, answer = self.ask(path)
                self.assertEqual(answer["outcome"], "REFUSED")
                self.assertEqual(answer["reason_code"], "UNREADABLE")
                self.assertEqual(code, 2)

    def test_a_row_of_the_wrong_type_refuses_rather_than_raising(self) -> None:
        """Presence was not enough, and checking only presence was the first repair.

        A row whose `endpoints` was `[{}]` passed a presence check and then died on
        `endpoint["activation"]`, which the CLI's catch-all labelled `UNKNOWN_RECORD`.
        Eleven other shapes raised `TypeError` or `AttributeError` and printed no JSON
        at all. Each case below is valid JSON, an object, with every key present.
        """
        cases = {
            "endpoints as a string": ("endpoints", "sov://x"),
            "endpoints as an object": ("endpoints", {"activation": "ACTIVE"}),
            "endpoints as an int": ("endpoints", 3),
            "an endpoint with no activation": ("endpoints", [{}]),
            "an endpoint that is a string": ("endpoints", ["ACTIVE"]),
            "actor_kinds as an int": ("actor_kinds", 2),
            "actor_kinds as null": ("actor_kinds", None),
            "shape as a string": ("shape", "READ"),
            "shape as a list": ("shape", []),
            "shape as null": ("shape", None),
            "shape.preconditions as an int": ("shape", {"preconditions": 1}),
            "shape.refusals as an int": ("shape", {"refusals": 1}),
        }
        for name, (key, value) in cases.items():
            with self.subTest(name):
                broken = dict(self.good)
                rows = [dict(row) for row in broken["capabilities"]]
                rows[0][key] = value
                broken["capabilities"] = rows
                code, answer = self.ask(self.write("row.json", json.dumps(broken)))
                self.assertEqual(answer["outcome"], "REFUSED", name)
                self.assertEqual(answer["reason_code"], "UNREADABLE", name)
                self.assertIn(answer["reason_code"], DECLARED["discover-operations"])
                self.assertEqual(code, 2)

    def test_a_caller_holding_nothing_learns_nothing_about_the_filesystem(self) -> None:
        """The map is read after the grant is shown, not before.

        `cli` built the map argument by reading the file, so it was read before
        `discover` was entered and therefore before the authority check. An ungranted
        caller could hand any path on the host to `--capability-map` and tell an absent
        file from an unparseable one from a directory, with the exception type in the
        message. Every one of them now answers the same way: you hold nothing.
        """
        answers = set()
        for path in (self.tmp / "not-here.json", self.tmp,
                     self.write("bad.json", "{not json"),
                     self.write("good.json", json.dumps(self.good))):
            out = StringIO()
            with contextlib.redirect_stdout(out):
                code = cli.main(["--root", str(self.store), "--node", NODE,
                                 "operations", "--operator", "stranger",
                                 "--capability-map", str(path)])
            answer = json.loads(out.getvalue())
            self.assertEqual(answer["reason_code"], "NO_LIVE_GRANT", str(path))
            self.assertEqual(code, 2)
            answers.add(json.dumps(answer, sort_keys=True))
        self.assertEqual(len(answers), 1, "the four paths are told apart")


class AuthorityBeforeTheRead(unittest.TestCase):
    """A caller holding nothing must learn nothing about which records exist.

    Two operations check authority before reading, because their grant's scope is
    known without a read: `console.revoke` scopes to the node, `console.open-thread`
    to the channel id the caller supplied. Reordering either one turns its refusal
    into an existence oracle for a caller with no grant at all, and the reorder
    otherwise passes every case in this suite.
    """

    def setUp(self) -> None:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        self.store = Path(holder.name) / "console"
        self.store.mkdir(parents=True)
        self.record = RecordService(empty_journal(self.store / "journal"))
        self.addCleanup(self.record.close)
        console = ConsoleService(self.record, self.store, NODE)
        console.grant("reader", "open:channel", "work", granted_by=BDO)
        self.channel = console.open_channel("reader", "work", "work")["channel_id"]
        self.grant = self.first_grant("reader", NODE)
        peer = ConsoleService(self.record, self.store, "node:peer")
        peer.grant("mallory", "open:channel", "work", granted_by="mallory")
        self.peer_channel = peer.open_channel("mallory", "work", "work")["channel_id"]
        peer.grant("mallory", "post:message", "t", granted_by="mallory")
        self.peer_grant = self.first_grant("mallory", "node:peer")

    def first_grant(self, operator_id: str, node_id: str) -> str:
        """One real grant id, so the probe below names something that exists."""
        return str(authority.held(self.record.reconstruct(), operator_id,
                                  node_id)[0]["grant_id"])

    def ask(self, arguments: list[str]) -> str:
        out = StringIO()
        with contextlib.redirect_stdout(out):
            cli.main(["--root", str(self.store), "--node", NODE, *arguments])
        return str(json.loads(out.getvalue())["reason_code"])

    def test_revoke_tells_an_ungranted_caller_only_that_it_holds_nothing(self) -> None:
        answers = {
            "a real grant of this node": self.ask(
                ["revoke", "--grant", self.grant, "--revoked-by", "stranger"]),
            "a real grant of another node": self.ask(
                ["revoke", "--grant", self.peer_grant, "--revoked-by", "stranger"]),
            "an id nothing carries": self.ask(
                ["revoke", "--grant", ABSENT_GRANT, "--revoked-by", "stranger"]),
        }
        self.assertEqual(set(answers.values()), {"NO_LIVE_GRANT"}, answers)

    def test_open_thread_tells_an_ungranted_caller_only_that_it_holds_nothing(self):
        answers = {
            "a real channel of this node": self.ask(
                ["open-thread", "--operator", "stranger", "--channel", self.channel,
                 "--title", "x"]),
            "a real channel of another node": self.ask(
                ["open-thread", "--operator", "stranger", "--channel",
                 self.peer_channel, "--title", "x"]),
            "an id nothing carries": self.ask(
                ["open-thread", "--operator", "stranger", "--channel", ABSENT_CHANNEL,
                 "--title", "x"]),
        }
        self.assertEqual(set(answers.values()), {"NO_LIVE_GRANT"}, answers)


class AUsageErrorIsStillOneJsonObject(unittest.TestCase):
    """A malformed invocation is answered, and is not answered as a refusal.

    `--node BAD` left a `ValueError` traceback and no JSON on every subcommand, and
    argparse's own errors - a missing flag, an unknown subcommand, no subcommand, a
    value outside `choices` - wrote their usage to stderr and exited 2, which is the
    code this module reserves for REFUSED. A machine caller could not tell a refused
    operation from a command it had typed wrongly.
    """

    def setUp(self) -> None:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        self.store = Path(holder.name) / "console"

    def answer(self, arguments: list[str]) -> tuple[int, dict[str, Any], str]:
        out, err = StringIO(), StringIO()
        try:
            with contextlib.redirect_stderr(err):
                with contextlib.redirect_stdout(out):
                    code = cli.main(arguments)
        except SystemExit as exited:
            code = int(exited.code or 0)
        return code, json.loads(out.getvalue()), err.getvalue()

    def test_a_node_that_is_not_a_node_identifier_answers_in_json(self) -> None:
        for node in ("BAD", "", "node:LOCAL", "node:local\n", "node:", "☃"):
            with self.subTest(node=node):
                code, answer, _ = self.answer(
                    ["--root", str(self.store), "--node", node, "grants",
                     "--reader", BDO])
                # A usage error, not a refusal: no console opened, so no operation was
                # attempted and no receipt carries a reason code for it.
                self.assertEqual(answer["outcome"], "USAGE_ERROR")
                self.assertNotIn("reason_code", answer)
                self.assertEqual(code, 1)

    def test_a_malformed_invocation_answers_in_json_and_not_at_the_refusal_code(self):
        cases = {
            "a missing required flag": ["--root", str(self.store), "grants"],
            "an unknown subcommand": ["--root", str(self.store), "nosuchcommand"],
            "no subcommand at all": ["--root", str(self.store)],
            "a value outside choices": ["--root", str(self.store), "open-session",
                                        "--operator", BDO, "--actor-kind", "ROBOT",
                                        "--binding", "b"],
            "an unknown flag": ["--root", str(self.store), "grants", "--reader", BDO,
                                "--nonsense", "x"],
        }
        for name, arguments in cases.items():
            with self.subTest(name):
                code, answer, err = self.answer(arguments)
                self.assertEqual(answer["outcome"], "USAGE_ERROR", name)
                self.assertNotIn("reason_code", answer)
                self.assertEqual(code, 1, name)
                self.assertEqual(err, "", "the usage message went to stderr as well")


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
