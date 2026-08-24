"""Console Service reference tests: operator continuity across sessions and operators.

These are the participant's own tests. They establish `BUILT` evidence about local
mechanics and are explicitly not independent of the code they exercise; `AGENTS.md`
reserves `WITNESSED` for an independent path and `RATIFIED` for Bdo.

Each declared behaviour has a positive case and a case proving the refusal. The
defeating cases are the ones named in `services/console/conformance/` seeds:
model-claims-without-proposal, projection-as-authority, history-erasure, and a
binding writing a post that carries no receipt.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import sqlite3
import sys
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).parents[2] / "record" / "src"))

from soveraeign_console_service import (  # noqa: E402
    AuthorityRefused,
    ConsoleService,
    ModelClaimWithoutProposal,
    PinIncomplete,
    Projection,
    SessionClosed,
    ThreadArchived,
    read_thread,
    session_context,
)
from soveraeign_record_service import BrokenChain, RecordService  # noqa: E402


class OperatorContinuity(unittest.TestCase):
    """Each test gets a private copy of one prepared journal.

    The fixture is built once and copied per test rather than rebuilt per test.
    The Record Service commits with `synchronous=FULL`, so every record costs an
    fsync - correct for a journal, and expensive enough at five records times
    thirty tests to push `scripts/verify.py` past its three-second budget. Copying
    keeps each test fully isolated; it only stops paying for the same setup thirty
    times.
    """

    @classmethod
    def setUpClass(cls):
        cls._template = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls._template.name) / "console"
        record = RecordService(root / "journal")
        console = ConsoleService(record, root, "node:test")
        console.grant("Bdo", "open-channel", "governance")
        channel = console.open_channel("Bdo", "governance", "governance")
        console.grant("Bdo", "open-thread", channel["channel_id"])
        thread = console.open_thread("Bdo", channel["channel_id"], "F0 closure")
        cls.prepared_grants = {operator: console.grant(operator, "post",
                                                       thread["thread_id"])["grant_id"]
                               for operator in ("Bdo", "sov")}
        cls.prepared_channel = channel["channel_id"]
        cls.prepared_thread = thread["thread_id"]
        cls.template_root = root
        record.close()

    @classmethod
    def tearDownClass(cls):
        cls._template.cleanup()

    def setUp(self):
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name) / "console"
        shutil.copytree(self.template_root, self.root)
        self.record = RecordService(self.root / "journal")
        self.console = ConsoleService(self.record, self.root, "node:test")
        self.channel = {"channel_id": self.prepared_channel}
        self.thread = {"thread_id": self.prepared_thread}
        self.grants = dict(self.prepared_grants)

    def tearDown(self):
        self.record.close()
        self.tmp.cleanup()

    def reopen(self) -> ConsoleService:
        """Close and reopen the store, the way a new process would."""
        self.record.close()
        self.record = RecordService(self.root / "journal")
        self.console = ConsoleService(self.record, self.root, "node:test")
        return self.console

    def receipts(self, event: str) -> list[dict]:
        return [entry["payload"] for entry in self.record.entries()
                if entry["kind"] == "RECEIPT" and entry["payload"]["event"] == event]

    # ---- cross-session continuity -----------------------------------------

    def test_a_later_session_sees_what_landed_while_it_was_closed(self):
        first = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post(first["session_id"], self.thread["thread_id"], b"opening the docket")
        self.console.close_session(first["session_id"])

        other = self.console.open_session("sov", "MODEL", "claude-code")
        self.console.post(other["session_id"], self.thread["thread_id"], b"landed while you were out")

        context = session_context(self.console, "Bdo")
        self.assertEqual([post["actor_id"] for post in context["unseen_posts"]], ["sov"])
        self.assertEqual(context["open_threads"][0]["post_count"], 2)
        self.assertFalse(context["authoritative"])

    def test_an_operator_does_not_read_their_own_turn_back_as_unseen(self):
        first = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.close_session(first["session_id"])
        second = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post(second["session_id"], self.thread["thread_id"], b"my own turn")
        self.assertEqual(session_context(self.console, "Bdo")["unseen_posts"], [])

    def test_continuity_survives_a_process_restart(self):
        first = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post(first["session_id"], self.thread["thread_id"], b"before the restart")
        self.console.close_session(first["session_id"])
        console = self.reopen()
        context = session_context(console, "Bdo")
        self.assertEqual(context["prior_sessions"][-1]["lifecycle"], "CLOSED")
        self.assertEqual(context["open_threads"][0]["title"], "F0 closure")

    def test_an_operator_with_no_closed_session_is_told_why_nothing_reads_as_seen(self):
        context = session_context(self.console, "Bdo")
        self.assertIsNone(context["cursor"])
        self.assertEqual(context["omissions"][0]["source"], "unread_cursor")

    # ---- two-binding parity ------------------------------------------------

    def test_a_human_post_and_a_model_post_take_the_same_transition(self):
        human = self.console.open_session("Bdo", "HUMAN", "human-binding")
        model = self.console.open_session("sov", "MODEL", "model-binding")
        self.console.post(human["session_id"], self.thread["thread_id"], b"a plain statement")
        self.console.post(model["session_id"], self.thread["thread_id"], b"a claim",
                          claims=True, proposal_id="proposal_1")

        posted = self.receipts("console.post")
        self.assertEqual({receipt["outcome"] for receipt in posted}, {"COMMITTED"})
        self.assertEqual({receipt["detail"]["operation_type"] for receipt in posted},
                         {"console.post"})
        self.assertEqual([receipt["detail"]["interface_id"] for receipt in posted],
                         ["human-binding", "model-binding"])
        self.assertTrue(all(receipt["detail"]["reason_code"] is None for receipt in posted))
        self.assertTrue(all(receipt["detail"]["effect_class"] == "RECORD_LOCAL"
                            for receipt in posted))

    def test_both_bindings_read_the_same_thread_in_the_same_order(self):
        human = self.console.open_session("Bdo", "HUMAN", "human-binding")
        model = self.console.open_session("sov", "MODEL", "model-binding")
        self.console.post(human["session_id"], self.thread["thread_id"], b"first")
        self.console.post(model["session_id"], self.thread["thread_id"], b"second")

        through_human = read_thread(self.console, self.thread["thread_id"], "human-binding")
        through_model = read_thread(self.console, self.thread["thread_id"], "model-binding")
        self.assertEqual([post["content_digest"] for post in through_human["posts"]],
                         [post["content_digest"] for post in through_model["posts"]])
        self.assertEqual([post["actor_kind"] for post in through_human["posts"]],
                         ["HUMAN", "MODEL"])
        self.assertEqual(through_human["posts"], through_model["posts"])

    def test_every_post_record_carries_a_receipt(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        for body in (b"one", b"two", b"three"):
            self.console.post(session["session_id"], self.thread["thread_id"], body)
        posts = [entry for entry in self.record.entries()
                 if entry["payload"].get("record_kind") == "post"]
        emitted = {address for receipt in self.receipts("console.post")
                   for address in receipt["detail"]["emitted_record_addresses"]}
        self.assertEqual({post["entry_id"] for post in posts}, emitted)

    # ---- payload custody ---------------------------------------------------

    def test_a_correction_appends_and_leaves_the_original_readable(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        original = self.console.post(session["session_id"], self.thread["thread_id"],
                                     b"the wrong number is 12")
        self.console.post(session["session_id"], self.thread["thread_id"],
                          b"correction: the number is 21")
        self.assertEqual(self.console.body(original["content_address"]),
                         b"the wrong number is 12")
        self.assertEqual(len(read_thread(self.console, self.thread["thread_id"])["posts"]), 2)

    def test_identical_bodies_share_one_address(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        first = self.console.post(session["session_id"], self.thread["thread_id"], b"same")
        second = self.console.post(session["session_id"], self.thread["thread_id"], b"same")
        self.assertEqual(first["content_address"], second["content_address"])
        self.assertNotEqual(first["post_id"], second["post_id"])

    # ---- projections are derived ------------------------------------------

    def test_a_projection_rebuilds_identically(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post(session["session_id"], self.thread["thread_id"], b"content")
        first = read_thread(self.console, self.thread["thread_id"])
        self.assertEqual(first, read_thread(self.console, self.thread["thread_id"]))
        self.assertFalse(first["authoritative"])
        self.assertEqual(first["rebuilt_from"], "record-service-journal")

    def test_a_rewritten_journal_stops_projecting_instead_of_lying(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post(session["session_id"], self.thread["thread_id"], b"honest")
        self.record.close()
        with sqlite3.connect(self.root / "journal" / "record-service.sqlite3") as db:
            db.execute("UPDATE journal SET payload_json=? WHERE kind='EVENT'",
                       ('{"record_kind":"post","tampered":true}',))
        self.record = RecordService(self.root / "journal")
        console = ConsoleService(self.record, self.root, "node:test")
        with self.assertRaises(BrokenChain):
            Projection(console)

    # ---- declared refusals -------------------------------------------------

    def test_a_model_post_that_claims_without_a_proposal_is_refused(self):
        model = self.console.open_session("sov", "MODEL", "model-binding")
        with self.assertRaises(ModelClaimWithoutProposal):
            self.console.post(model["session_id"], self.thread["thread_id"],
                              b"this is settled", claims=True)
        refused = self.receipts("console.post")
        self.assertEqual(refused[0]["outcome"], "REFUSED")
        self.assertEqual(refused[0]["detail"]["reason_code"], "CLAIM_WITHOUT_PROPOSAL")
        self.assertEqual(read_thread(self.console, self.thread["thread_id"])["posts"], [])

    def test_a_human_post_that_claims_needs_no_proposal(self):
        human = self.console.open_session("Bdo", "HUMAN", "human-binding")
        post = self.console.post(human["session_id"], self.thread["thread_id"],
                                 b"I accept this", claims=True)
        self.assertIsNone(post["proposal_id"])
        self.assertEqual(post["standing"], "RECORDED")

    def test_a_post_without_a_live_grant_is_refused(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.revoke(self.grants["Bdo"])
        with self.assertRaises(AuthorityRefused):
            self.console.post(session["session_id"], self.thread["thread_id"], b"ungranted")

    def test_a_post_through_a_closed_session_is_refused(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.close_session(session["session_id"])
        with self.assertRaises(SessionClosed):
            self.console.post(session["session_id"], self.thread["thread_id"], b"too late")

    def test_a_post_into_an_archived_thread_is_refused(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.archive_thread("Bdo", self.thread["thread_id"])
        with self.assertRaises(ThreadArchived):
            self.console.post(session["session_id"], self.thread["thread_id"], b"reopened?")
        self.assertEqual(
            read_thread(self.console, self.thread["thread_id"])["lifecycle"], "ARCHIVED")

    def test_a_thread_pinned_without_a_digest_is_refused(self):
        with self.assertRaises(PinIncomplete):
            self.console.open_thread("Bdo", self.channel["channel_id"], "pinned",
                                     pinned_address="asset/v1")

    def test_a_grant_outlives_the_process_that_recorded_it(self):
        console = self.reopen()
        session = console.open_session("Bdo", "HUMAN", "cli")
        post = console.post(session["session_id"], self.thread["thread_id"], b"still granted")
        self.assertEqual(post["standing"], "RECORDED")
        self.assertEqual({record["capability"] for record in console.grants("Bdo")},
                         {"open-channel", "open-thread", "post"})

    def test_a_revocation_leaves_the_operation_it_already_admitted_standing(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        before = self.console.post(session["session_id"], self.thread["thread_id"], b"admitted")
        self.console.revoke(self.grants["Bdo"])
        with self.assertRaises(AuthorityRefused):
            self.console.post(session["session_id"], self.thread["thread_id"], b"refused")
        self.assertEqual(self.console.body(before["content_address"]), b"admitted")
        self.assertNotIn("post", {record["capability"]
                                  for record in self.console.grants("Bdo")})
        still_there = read_thread(self.console, self.thread["thread_id"])["posts"]
        self.assertEqual([post["post_id"] for post in still_there], [before["post_id"]])

    def test_opening_a_channel_without_a_grant_is_refused(self):
        with self.assertRaises(AuthorityRefused):
            self.console.open_channel("stranger", "quiet", "governance")


if __name__ == "__main__":
    unittest.main()
