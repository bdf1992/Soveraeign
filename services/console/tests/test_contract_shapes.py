"""Check the records this service emits against the schemas it declares.

The schemas in `services/console/contracts/` were written before there was an
implementation. A service whose records do not validate against its own declared
contract has two contradictory descriptions of itself, and the schema is the one
that other participants read. So the projection is driven against the real schema
files with the repository's own validator rather than against a restatement of
them.

Every case has a defeating counterpart. A validator that only ever sees valid
instances proves nothing about whether it is checking anything.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parents[2] / "record" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from soveraeign_console_service import ConsoleService  # noqa: E402
from soveraeign_console_service import contract  # noqa: E402
from soveraeign_console_service import continuity  # noqa: E402
from soveraeign_console_service.refusals import (  # noqa: E402
    AuthorityRefused,
    ForeignNodeRecord,
)
from soveraeign_record_service import RecordService  # noqa: E402
from sovkernel import jsonschema  # noqa: E402

CONTRACTS = Path(__file__).parents[1] / "contracts"
# The node this walk's console serves. Every channel and thread it emits must say so
# (decisions/0039); a record that did not could not be told from a peer's.
NODE = "node:test"


def schema(name: str) -> dict:
    return json.loads((CONTRACTS / name).read_text("utf-8"))


class DeclaredRecordShapes(unittest.TestCase):
    """One recorded walk, read many ways.

    Every case here reads the same projection and none of them mutate it, so the
    walk is driven once. Rebuilding it per test would buy no isolation and would
    cost an fsync per record against the verification budget.
    """

    @classmethod
    def setUpClass(cls):
        cls.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls.tmp.name) / "console"
        cls.record = RecordService(root / "journal")
        console = ConsoleService(cls.record, root, NODE)
        console.grant("Bdo", "open:channel", "governance")
        channel = console.open_channel("Bdo", "governance", "governance")
        console.grant("Bdo", "open:thread", channel["channel_id"])
        thread = console.open_thread("Bdo", channel["channel_id"], "F0 closure",
                                     pinned_address="asset/v1", pinned_digest="sha256:ab")
        console.grant("Bdo", "post:message", thread["thread_id"])
        console.grant("sov", "post:message", thread["thread_id"])
        human = console.open_session("Bdo", "HUMAN", "human-binding")
        model = console.open_session("sov", "MODEL", "model-binding")
        console.post(human["session_id"], thread["thread_id"], b"a plain statement",
                     mentions=["sov"])
        console.post(model["session_id"], thread["thread_id"], b"a claim",
                     claims=True, proposal_id="proposal_1")
        console.grant("Bdo", "publish:thread", thread["thread_id"])
        cls.published = console.publish_thread("Bdo", thread["thread_id"])
        second = console.open_thread("Bdo", channel["channel_id"], "withdrawn work",
                                     pinned_address="asset/v2", pinned_digest="sha256:cd")
        console.grant("Bdo", "publish:thread", second["thread_id"])
        withdrawn = console.publish_thread("Bdo", second["thread_id"])
        console.withdraw_publication("Bdo", withdrawn["publication_id"])
        cls.withdrawn_id = withdrawn["publication_id"]
        console.close_session(human["session_id"])
        cls.records = contract.records(cls.record.reconstruct())

    @classmethod
    def tearDownClass(cls):
        cls.record.close()
        cls.tmp.cleanup()

    def assertValid(self, instance, schema_name):
        errors = jsonschema.validate(instance, schema(schema_name))
        self.assertEqual(errors, [], f"{schema_name}: {errors}")

    def assertRejected(self, instance, schema_name):
        self.assertNotEqual(jsonschema.validate(instance, schema(schema_name)), [])

    # ---- positive: what the service actually emits -------------------------

    def test_emitted_channels_validate(self):
        self.assertEqual(len(self.records["channels"]), 1)
        for record in self.records["channels"]:
            self.assertValid(record, "channel.schema.json")

    def test_emitted_threads_validate_pinned(self):
        for record in self.records["threads"]:
            self.assertValid(record, "thread.schema.json")
        self.assertEqual({record["pinned_digest"] for record in self.records["threads"]},
                         {"sha256:ab", "sha256:cd"})

    def test_emitted_sessions_validate_open_and_closed(self):
        lifecycles = {record["lifecycle"] for record in self.records["operator_sessions"]}
        self.assertEqual(lifecycles, {"OPEN", "CLOSED"})
        for record in self.records["operator_sessions"]:
            self.assertValid(record, "operator-session.schema.json")

    def test_emitted_posts_validate_and_name_their_receipt(self):
        self.assertEqual(len(self.records["posts"]), 2)
        for record in self.records["posts"]:
            self.assertValid(record, "post.schema.json")
            self.assertTrue(record["receipt_id"].startswith("entry_"))

    def test_a_model_post_carries_a_proposal_and_a_human_post_need_not(self):
        by_kind = {record["actor_kind"]: record for record in self.records["posts"]}
        self.assertEqual(by_kind["MODEL"]["proposal_id"], "proposal_1")
        self.assertIsNone(by_kind["HUMAN"]["proposal_id"])
        self.assertEqual({record["standing"] for record in self.records["posts"]}, {"RECORDED"})

    def test_emitted_channels_and_threads_name_this_console_s_node(self):
        for group in ("channels", "threads"):
            for record in self.records[group]:
                self.assertEqual(record["node_id"], NODE, f"{group}: {record}")

    def test_the_local_walk_holds_no_foreign_record(self):
        self.assertEqual(contract.foreign_records(self.records, NODE), [])

    def test_emitted_publications_validate(self):
        self.assertEqual(len(self.records["publications"]), 2)
        for record in self.records["publications"]:
            self.assertValid(record, "publication.schema.json")

    def test_a_withdrawn_publication_keeps_its_record_and_leaves_the_view(self):
        """Withdrawal appends. The mark stays readable; only what renders changes."""
        by_id = {record["publication_id"]: record
                 for record in self.records["publications"]}
        self.assertEqual(by_id[self.withdrawn_id]["lifecycle"], "WITHDRAWN")
        self.assertIsNotNone(by_id[self.withdrawn_id]["withdrawn_at"])
        rendered = contract.published_threads(self.records)
        self.assertEqual([record["thread_id"] for record in rendered],
                         [self.published["thread_id"]])

    def test_published_threads_carry_the_node_their_thread_belongs_to(self):
        for record in contract.published_threads(self.records):
            self.assertEqual(record["node_id"], NODE)

    def test_the_outward_view_separates_never_published_from_taken_down(self):
        """A reader can tell the two apart without being handed the journal."""
        console = ConsoleService(self.record, Path(self.tmp.name) / "console", NODE)
        view = continuity.published_threads(console)
        self.assertFalse(view["authoritative"])
        self.assertEqual(view["node_id"], NODE)
        self.assertEqual([record["thread_id"] for record in view["published"]],
                         [self.published["thread_id"]])
        self.assertEqual(len(view["omissions"]), 1)

    def test_the_projection_carries_no_journal_machinery(self):
        leaked = {"record_kind", "entry_id", "entry_digest", "session_id", "binding_id"}
        for group in ("channels", "threads", "posts"):
            for record in self.records[group]:
                self.assertEqual(leaked & set(record), set(), f"{group}: {record}")

    # ---- defeating: the schemas reject what the service must never emit -----

    def test_a_post_without_a_receipt_is_rejected(self):
        broken = dict(self.records["posts"][0], receipt_id="")
        self.assertRejected(broken, "post.schema.json")

    def test_a_post_claiming_standing_above_recorded_is_rejected(self):
        broken = dict(self.records["posts"][0], standing="EFFECTIVE_BY_DEFAULT")
        self.assertRejected(broken, "post.schema.json")

    def test_a_thread_pinned_without_a_digest_is_rejected(self):
        broken = dict(self.records["threads"][0], pinned_digest=None)
        self.assertRejected(broken, "thread.schema.json")

    def test_a_session_with_an_unknown_actor_kind_is_rejected(self):
        broken = dict(self.records["operator_sessions"][0], actor_kind="AGENT")
        self.assertRejected(broken, "operator-session.schema.json")

    def test_a_record_carrying_an_extra_field_is_rejected(self):
        broken = dict(self.records["channels"][0], settled_by="itself")
        self.assertRejected(broken, "channel.schema.json")

    def test_a_publication_marked_published_but_carrying_a_withdrawal_is_rejected(self):
        live = next(record for record in self.records["publications"]
                    if record["lifecycle"] == "PUBLISHED")
        broken = dict(live, withdrawn_at="2026-08-23T12:00:00Z")
        self.assertRejected(broken, "publication.schema.json")

    def test_a_publication_withdrawn_without_a_time_is_rejected(self):
        gone = next(record for record in self.records["publications"]
                    if record["lifecycle"] == "WITHDRAWN")
        self.assertRejected(dict(gone, withdrawn_at=None), "publication.schema.json")

    def test_a_publication_offering_a_second_visibility_is_rejected(self):
        """Degrees of visibility would be an access-control system; grants are that."""
        live = next(record for record in self.records["publications"]
                    if record["lifecycle"] == "PUBLISHED")
        self.assertRejected(dict(live, visibility="UNLISTED"), "publication.schema.json")

    def test_a_channel_without_a_node_is_rejected(self):
        """A record that does not say which node it is from cannot survive a crossing."""
        broken = {k: v for k, v in self.records["channels"][0].items() if k != "node_id"}
        self.assertRejected(broken, "channel.schema.json")

    def test_a_thread_whose_node_is_not_a_node_identifier_is_rejected(self):
        broken = dict(self.records["threads"][0], node_id="home")
        self.assertRejected(broken, "thread.schema.json")

    def test_a_thread_from_another_node_is_named_as_foreign(self):
        """Schema-valid and individually well formed; only the node scope shows it."""
        foreign = dict(self.records["threads"][0], node_id="node:peer-one")
        self.assertValid(foreign, "thread.schema.json")
        named = contract.foreign_records(
            dict(self.records, threads=[foreign]), NODE)
        self.assertTrue(any("node:peer-one" in line for line in named), named)

    def test_a_thread_disagreeing_with_its_channel_is_named(self):
        """Both records claim a node; they cannot both be right, and neither settles."""
        channel = dict(self.records["channels"][0], node_id="node:peer-one")
        thread = self.records["threads"][0]
        named = contract.foreign_records(
            dict(self.records, channels=[channel], threads=[thread]), NODE)
        self.assertTrue(any("claims" in line for line in named), named)


class NodeScopeRefusals(unittest.TestCase):
    """A console serves one node and refuses to act on another node's records."""

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name) / "console"
        self.record = RecordService(self.root / "journal")

    def tearDown(self):
        self.record.close()
        self.tmp.cleanup()

    def test_a_console_cannot_be_opened_without_a_node_identifier(self):
        with self.assertRaises(ValueError):
            ConsoleService(self.record, self.root, "home")

    def test_publishing_a_thread_from_another_node_is_refused(self):
        """Publishing a peer's thread would republish their record under this node's name."""
        console = ConsoleService(self.record, self.root, NODE)
        console.grant("Bdo", "open:channel", "governance")
        channel = console.open_channel("Bdo", "governance", "governance")
        console.grant("Bdo", "open:thread", channel["channel_id"])
        thread = console.open_thread("Bdo", channel["channel_id"], "local work")

        peer = ConsoleService(self.record, self.root, "node:peer-one")
        peer.grant("Bdo", "publish:thread", thread["thread_id"])
        with self.assertRaises(ForeignNodeRecord) as refused:
            peer.publish_thread("Bdo", thread["thread_id"])
        self.assertEqual(refused.exception.reason_code, "FOREIGN_NODE_RECORD")

    def test_publishing_without_a_grant_is_refused(self):
        """Publishing is an outward effect and takes its own capability, not open-thread's."""
        console = ConsoleService(self.record, self.root, NODE)
        console.grant("Bdo", "open:channel", "governance")
        channel = console.open_channel("Bdo", "governance", "governance")
        console.grant("Bdo", "open:thread", channel["channel_id"])
        thread = console.open_thread("Bdo", channel["channel_id"], "unpublishable")
        with self.assertRaises(AuthorityRefused):
            console.publish_thread("Bdo", thread["thread_id"])

    def test_an_ungranted_transition_leaves_a_refused_receipt(self):
        """The defeating case for `append.py`'s own rule.

        Every other refusal in this service goes through `append.refuse`, which writes
        a REFUSED receipt before raising. `authority.check` reads the journal and
        cannot append to it, so a NO_LIVE_GRANT used to leave nothing behind, and a
        transition that refused was indistinguishable from one nobody attempted.
        """
        console = ConsoleService(self.record, self.root, NODE)
        before = len(self.record.reconstruct())
        with self.assertRaises(AuthorityRefused):
            console.open_channel("Bdo", "governance", "governance")

        entries = self.record.reconstruct()
        self.assertEqual(len(entries), before + 1, "the refusal left no trace")
        receipt = entries[-1]
        self.assertEqual(receipt["kind"], "RECEIPT")
        self.assertEqual(receipt["payload"]["outcome"], "REFUSED")
        self.assertEqual(receipt["payload"]["detail"]["reason_code"], "NO_LIVE_GRANT")
        self.assertEqual(receipt["payload"]["event"], "console.open-channel")
        self.assertEqual(receipt["actor"], "Bdo")

    def test_every_ungranted_transition_is_written_down_not_just_the_first(self):
        """One refusal per attempt, naming the transition attempted.

        A single refusal path would be easy to fix in one place and leave wrong in
        five, so each transition that checks a grant is driven without one.
        """
        console = ConsoleService(self.record, self.root, NODE)
        console.grant("Bdo", "open:channel", "governance")
        channel = console.open_channel("Bdo", "governance", "governance")["channel_id"]
        console.grant("Bdo", "open:thread", channel)
        thread = console.open_thread("Bdo", channel, "what a refusal leaves")["thread_id"]
        session = console.open_session("Ana", "HUMAN", "binding:test")["session_id"]

        attempts = {
            "console.open-channel": lambda: console.open_channel("Ana", "ops", "ops"),
            "console.open-thread": lambda: console.open_thread("Ana", channel, "no"),
            "console.archive-thread": lambda: console.archive_thread("Ana", thread),
            "console.publish-thread": lambda: console.publish_thread("Ana", thread),
            "console.post": lambda: console.post(session, thread, b"unauthorised"),
        }
        for event, attempt in attempts.items():
            with self.subTest(event=event):
                before = len(self.record.reconstruct())
                with self.assertRaises(AuthorityRefused):
                    attempt()
                entries = self.record.reconstruct()
                self.assertEqual(len(entries), before + 1)
                payload = entries[-1]["payload"]
                self.assertEqual(payload["outcome"], "REFUSED")
                self.assertEqual(payload["event"], event)
                self.assertEqual(payload["detail"]["reason_code"], "NO_LIVE_GRANT")

    def test_a_refused_transition_emits_no_record_of_its_own(self):
        """The refusal is written; the thing refused is not.

        The counterpart to the case above: a receipt saying a channel was refused must
        not arrive alongside the channel it refused.
        """
        console = ConsoleService(self.record, self.root, NODE)
        with self.assertRaises(AuthorityRefused):
            console.open_channel("Bdo", "governance", "governance")
        kinds = [entry["kind"] for entry in self.record.reconstruct()]
        self.assertEqual(kinds, ["RECEIPT"])
        self.assertEqual(contract.records(self.record.reconstruct())["channels"], [])

    def test_archiving_a_thread_from_another_node_is_refused(self):
        """The refusal a crossing needs: a local seat may not close a peer's thread."""
        console = ConsoleService(self.record, self.root, NODE)
        console.grant("Bdo", "open:channel", "governance")
        channel = console.open_channel("Bdo", "governance", "governance")
        console.grant("Bdo", "open:thread", channel["channel_id"])
        thread = console.open_thread("Bdo", channel["channel_id"], "F0 closure")

        peer = ConsoleService(self.record, self.root, "node:peer-one")
        with self.assertRaises(ForeignNodeRecord) as refused:
            peer.archive_thread("Bdo", thread["thread_id"])
        self.assertEqual(refused.exception.reason_code, "FOREIGN_NODE_RECORD")


if __name__ == "__main__":
    unittest.main()
