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
    ActorAttributionMismatch,
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
    thirty tests to push `scripts/verify.py` past its budget. Copying
    keeps each test fully isolated; it only stops paying for the same setup thirty
    times.
    """

    @classmethod
    def setUpClass(cls):
        cls._template = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls._template.name) / "console"
        record = RecordService(root / "journal")
        console = ConsoleService(record, root, "node:test")
        console.grant("Bdo", "open:channel", "governance", "Bdo")
        channel = console.open_channel("Bdo", "governance", "governance")
        console.grant("Bdo", "open:thread", channel["channel_id"], "Bdo")
        thread = console.open_thread("Bdo", channel["channel_id"], "F0 closure")
        cls.prepared_grants = {operator: console.grant(operator, "post:message",
                                                       thread["thread_id"], "Bdo")["grant_id"]
                               for operator in ("Bdo", "sov")}
        # The session lifecycle and the reads are guarded as of 2026-08-25, so the
        # fixture operators hold what those operations cost. These are setup grants
        # for the continuity path; the cases below still prove their own refusals.
        for operator in ("Bdo", "sov"):
            for capability in ("open:session", "close:session", "read:session"):
                console.grant(operator, capability, operator, "Bdo")
            console.grant(operator, "read:authority", "node:test", "Bdo")
            console.grant(operator, "read:thread", thread["thread_id"], "Bdo")
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
        self.console.post("Bdo", first["session_id"], self.thread["thread_id"],
                          b"opening the docket")
        self.console.close_session("Bdo", first["session_id"])

        other = self.console.open_session("sov", "MODEL", "claude-code")
        self.console.post("sov", other["session_id"], self.thread["thread_id"],
                          b"landed while you were out")

        context = session_context(self.console, "Bdo")
        self.assertEqual([post["actor_id"] for post in context["unseen_posts"]], ["sov"])
        self.assertEqual(context["open_threads"][0]["post_count"], 2)
        self.assertFalse(context["authoritative"])

    def test_an_operator_does_not_read_their_own_turn_back_as_unseen(self):
        first = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.close_session("Bdo", first["session_id"])
        second = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post("Bdo", second["session_id"], self.thread["thread_id"],
                          b"my own turn")
        self.assertEqual(session_context(self.console, "Bdo")["unseen_posts"], [])

    def test_continuity_survives_a_process_restart(self):
        first = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post("Bdo", first["session_id"], self.thread["thread_id"],
                          b"before the restart")
        self.console.close_session("Bdo", first["session_id"])
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
        self.console.post("Bdo", human["session_id"], self.thread["thread_id"], b"a plain statement")
        self.console.post("sov", model["session_id"], self.thread["thread_id"], b"a claim",
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
        self.console.post("Bdo", human["session_id"], self.thread["thread_id"], b"first")
        self.console.post("sov", model["session_id"], self.thread["thread_id"], b"second")

        through_human = read_thread(self.console, self.thread["thread_id"], "human-binding",
                                    operator_id="Bdo")
        through_model = read_thread(self.console, self.thread["thread_id"], "model-binding",
                                    operator_id="sov")
        self.assertEqual([post["content_digest"] for post in through_human["posts"]],
                         [post["content_digest"] for post in through_model["posts"]])
        self.assertEqual([post["actor_kind"] for post in through_human["posts"]],
                         ["HUMAN", "MODEL"])
        self.assertEqual(through_human["posts"], through_model["posts"])

    def test_every_post_record_carries_a_receipt(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        for body in (b"one", b"two", b"three"):
            self.console.post("Bdo", session["session_id"], self.thread["thread_id"], body)
        posts = [entry for entry in self.record.entries()
                 if entry["payload"].get("record_kind") == "post"]
        emitted = {address for receipt in self.receipts("console.post")
                   for address in receipt["detail"]["emitted_record_addresses"]}
        self.assertEqual({post["entry_id"] for post in posts}, emitted)

    # ---- payload custody ---------------------------------------------------

    def test_a_correction_appends_and_leaves_the_original_readable(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        original = self.console.post("Bdo", session["session_id"], self.thread["thread_id"],
                                     b"the wrong number is 12")
        self.console.post("Bdo", session["session_id"], self.thread["thread_id"],
                          b"correction: the number is 21")
        self.assertEqual(self.console.body(original["content_address"]),
                         b"the wrong number is 12")
        self.assertEqual(len(read_thread(self.console, self.thread["thread_id"], operator_id="Bdo")["posts"]), 2)

    def test_identical_bodies_share_one_address(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        first = self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"same")
        second = self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"same")
        self.assertEqual(first["content_address"], second["content_address"])
        self.assertNotEqual(first["post_id"], second["post_id"])

    # ---- projections are derived ------------------------------------------

    def test_a_projection_rebuilds_identically(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"content")
        first = read_thread(self.console, self.thread["thread_id"], operator_id="Bdo")
        self.assertEqual(first, read_thread(self.console, self.thread["thread_id"], operator_id="Bdo"))
        self.assertFalse(first["authoritative"])
        self.assertEqual(first["rebuilt_from"], "record-service-journal")

    def test_a_rewritten_journal_stops_projecting_instead_of_lying(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"honest")
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
            self.console.post("sov", model["session_id"], self.thread["thread_id"],
                              b"this is settled", claims=True)
        refused = self.receipts("console.post")
        self.assertEqual(refused[0]["outcome"], "REFUSED")
        self.assertEqual(refused[0]["detail"]["reason_code"], "CLAIM_WITHOUT_PROPOSAL")
        self.assertEqual(read_thread(self.console, self.thread["thread_id"], operator_id="Bdo")["posts"], [])

    def test_a_human_post_that_claims_needs_no_proposal(self):
        human = self.console.open_session("Bdo", "HUMAN", "human-binding")
        post = self.console.post("Bdo", human["session_id"], self.thread["thread_id"],
                                 b"I accept this", claims=True)
        self.assertIsNone(post["proposal_id"])
        self.assertEqual(post["standing"], "RECORDED")

    def test_a_post_without_a_live_grant_is_refused(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.revoke(self.grants["Bdo"], "Bdo")
        with self.assertRaises(AuthorityRefused):
            self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"ungranted")

    def test_posting_through_another_operators_session_is_refused(self):
        """A session identifies an operator; holding its id does not make you one.

        `sov` holds `post:message` on this thread in its own right, so the refusal
        here is about attribution and not about the permit - which is what makes it
        a defeating case rather than a restatement of the grant check. Without it
        the post commits carrying `sov` as actor and Bdo's session and binding, and
        a later reader cannot tell whose turn it was.

        The Gateway route has refused this since it was written
        (`test_routes.py`, ACTOR_ATTRIBUTION_MISMATCH). The console path added the
        same check on 2026-08-25 and nothing drove it until now.
        """
        human = self.console.open_session("Bdo", "HUMAN", "human-binding")
        held = {record["capability"] for record
                in self.console.grants(reader_id="sov", operator_id="sov")}
        self.assertIn("post:message", held)
        before = len(self.receipts("console.post"))
        with self.assertRaises(ActorAttributionMismatch) as refused:
            self.console.post("sov", human["session_id"], self.thread["thread_id"],
                              b"not my session")
        self.assertEqual(refused.exception.reason_code, "ACTOR_ATTRIBUTION_MISMATCH")
        self.assertIn("belongs to Bdo", str(refused.exception))

        receipts = self.receipts("console.post")
        self.assertEqual(len(receipts), before + 1, "the refusal left no trace")
        self.assertEqual(receipts[-1]["outcome"], "REFUSED")
        self.assertEqual(receipts[-1]["detail"]["reason_code"],
                         "ACTOR_ATTRIBUTION_MISMATCH")
        self.assertEqual(
            read_thread(self.console, self.thread["thread_id"],
                        operator_id="Bdo")["posts"], [],
            "a refused post reached the thread")

    def test_posting_through_your_own_session_is_admitted(self):
        """The positive half, so the case above cannot pass by refusing everything."""
        model = self.console.open_session("sov", "MODEL", "model-binding")
        written = self.console.post("sov", model["session_id"],
                                    self.thread["thread_id"], b"my own session")
        self.assertEqual(written["actor_id"], "sov")
        self.assertEqual(written["session_id"], model["session_id"])

    def test_a_post_through_a_closed_session_is_refused(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.close_session("Bdo", session["session_id"])
        with self.assertRaises(SessionClosed):
            self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"too late")

    def test_a_post_into_an_archived_thread_is_refused(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        self.console.grant("Bdo", "archive:thread", self.channel["channel_id"], "Bdo")
        self.console.archive_thread("Bdo", self.thread["thread_id"])
        with self.assertRaises(ThreadArchived):
            self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"reopened?")
        self.assertEqual(
            read_thread(self.console, self.thread["thread_id"], operator_id="Bdo")["lifecycle"], "ARCHIVED")

    def test_opening_a_thread_does_not_carry_the_right_to_archive_it(self):
        """Archiving THE thread needs its own grant (Bdo, 2026-08-24; decisions/0054).

        The fixture operator holds `open:thread` over this channel and opened the thread
        under it. Archiving stops every operator posting into it, so it is a wider act
        than opening one and no longer rides on the opener's grant.
        """
        held = {record["capability"] for record in self.console.grants(reader_id="Bdo", operator_id="Bdo")}
        self.assertIn("open:thread", held)
        self.assertNotIn("archive:thread", held)
        with self.assertRaises(AuthorityRefused) as refused:
            self.console.archive_thread("Bdo", self.thread["thread_id"])
        self.assertIn("archive:thread", str(refused.exception))
        self.assertEqual(
            read_thread(self.console, self.thread["thread_id"], operator_id="Bdo")["lifecycle"], "OPEN")

    def test_a_thread_pinned_without_a_digest_is_refused(self):
        with self.assertRaises(PinIncomplete):
            self.console.open_thread("Bdo", self.channel["channel_id"], "pinned",
                                     pinned_address="asset/v1")

    def test_a_grant_outlives_the_process_that_recorded_it(self):
        console = self.reopen()
        session = console.open_session("Bdo", "HUMAN", "cli")
        post = console.post("Bdo", session["session_id"], self.thread["thread_id"], b"still granted")
        self.assertEqual(post["standing"], "RECORDED")
        # `grant:authority` and `revoke:authority` are the genesis pair: this fixture's
        # first grant recorded Bdo as the node's root issuer (`authority.py`, Bootstrap).
        self.assertEqual({record["capability"] for record
                          in console.grants(reader_id="Bdo", operator_id="Bdo")},
                         {"grant:authority", "revoke:authority", "open:channel",
                          "open:thread", "post:message", "open:session", "close:session",
                          "read:session", "read:authority", "read:thread"})

    def test_the_grant_named_on_the_receipt_is_the_one_that_admitted_the_operation(self):
        """`check` claims the newest matching grant wins; the receipt has to show it.

        Mutation scoring found this unasserted on 2026-08-24: `check` could return
        nothing at all and the suite stayed green, so a receipt could name no grant -
        or the revoked one - while the operation still committed.
        """
        stale = self.grants["Bdo"]
        self.console.revoke(stale, "Bdo")
        fresh = self.console.grant("Bdo", "post:message",
                                   self.thread["thread_id"], "Bdo")["grant_id"]
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        post = self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"regranted")
        receipt = self.receipts("console.post")[-1]
        self.assertEqual(receipt["detail"]["authority_grant_ids"], [fresh])
        self.assertNotIn(stale, receipt["detail"]["authority_grant_ids"])
        self.assertEqual(post["standing"], "RECORDED")

    def test_a_revocation_leaves_the_operation_it_already_admitted_standing(self):
        session = self.console.open_session("Bdo", "HUMAN", "cli")
        before = self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"admitted")
        self.console.revoke(self.grants["Bdo"], "Bdo")
        with self.assertRaises(AuthorityRefused):
            self.console.post("Bdo", session["session_id"], self.thread["thread_id"], b"refused")
        self.assertEqual(self.console.body(before["content_address"]), b"admitted")
        self.assertNotIn("post", {record["capability"]
                                  for record in self.console.grants(reader_id="Bdo", operator_id="Bdo")})
        still_there = read_thread(self.console, self.thread["thread_id"], operator_id="Bdo")["posts"]
        self.assertEqual([post["post_id"] for post in still_there], [before["post_id"]])

    def test_opening_a_channel_without_a_grant_is_refused(self):
        with self.assertRaises(AuthorityRefused):
            self.console.open_channel("stranger", "quiet", "governance")


if __name__ == "__main__":
    unittest.main()
