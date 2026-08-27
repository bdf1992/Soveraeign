"""A grant is honoured only by the node whose permits office minted it.

The defect this exists for: a grant is matched on operator, capability and scope,
and none of those mention a node. The console's node identifier is supplied by
whoever opened it - a constructor argument, `--node` on the CLI - so before
2026-08-25 a caller could open a console under any identifier at all, mint itself
a grant there, and then reopen the same store under the real node's identifier and
spend it. An independent witness reproduced that through the shipped CLI against
one `--root`, and it defeated the six operations that were already enforcing as
well as the nine guarded that day.

Two kinds of case here, and the difference is the point.

`ReproducedThroughTheCLI` drives the exact three commands the witness sent, in
order, through the same entry point an operator has. It is one instance.

`NodeNamespacePartition` drives the property that instance is an instance of. The
consumer of a node identifier is `authority.check`, and what it does with one is
compare it to a stored string with `==` and nothing else - no case folding, no
whitespace stripping, no prefix or pattern reading. So the namespaces it induces
are exactly string identity, and the testable claim is that for any two spellings
that differ by any byte, a grant minted under one satisfies no check under the
other, while a grant minted under a spelling does satisfy checks under that same
spelling. The corpus below is evidence for that claim, not the definition of it: a
spelling nobody thought of is covered by the property, which is the difference
between this and a list of the escapes somebody was already shown.

What none of it establishes is that a node identifier is *true*. Nothing in the
record attests it and there is no Identity service; see `authority.py` and
`services/console/KNOWN-GAPS.md`. What keeps the partition from being walked
around is the bootstrap: opening a node's permits office is once-ever and
recorded, so a caller asserting a name whose office is already open meets a
`grant:authority` it does not hold.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import authority, contract  # noqa: E402
from soveraeign_console_service.continuity import (  # noqa: E402
    published_threads,
    read_thread,
    session_context,
)
from soveraeign_console_service.core import ConsoleService  # noqa: E402
from soveraeign_console_service.refusals import (  # noqa: E402
    AuthorityRefused,
    ForeignNodeRecord,
    LastIssuerStanding,
    UnknownRecord,
)
from soveraeign_record_service import RecordService  # noqa: E402

HOME = "node:local"
EVIL = "node:evil"
MALLORY = "Mallory"

#: Spellings a node identifier could arrive as. Each is either refused at the
#: constructor or is a node of its own; none of them may reach `node:local`'s grants.
#: Drawn to cover the ways a string comparison leaks elsewhere - case, surrounding
#: whitespace, a line terminator, unicode that renders alike, prefix and suffix of a
#: real name, path and pattern punctuation - rather than to list known attacks.
SPELLINGS = (
    "node:local" + chr(10),
    "node:local" + chr(13),
    "node:local" + chr(9),
    "node:LOCAL",
    "NODE:local",
    "node:local ",
    " node:local",
    "node:local-",
    "node:loca",
    "node:localx",
    "node:l0cal",
    "node:löcal",
    "node:ｌｏcal",
    "node:local​",
    "node:",
    "node:local:evil",
    "node:local/../evil",
    "node:local/evil",
    "node:*",
    "node:local*",
    "node:evil",
    "",
)


class NodeNamespacePartition(unittest.TestCase):
    """The property: the namespace a grant lands in is the node identifier, exactly."""

    #: Built once and copied. Opening the office costs three fsynced records and no
    #: case here needs a different one; see `OperatorContinuity` for the pattern.
    @classmethod
    def setUpClass(cls) -> None:
        cls._template = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls._template.name) / "fixture"
        record = RecordService(root / "journal")
        home = ConsoleService(record, root / "home", HOME)
        # The home node's office is opened by its own root, which is what an attacker
        # asserting this name later has to get past.
        home.grant("Bdo", "read:thread", HOME, "Bdo")
        record.close()
        cls.template_root = root

    @classmethod
    def tearDownClass(cls) -> None:
        cls._template.cleanup()

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name) / "fixture"
        shutil.copytree(self.template_root, self.root)
        self.record = RecordService(self.root / "journal")
        self.addCleanup(self.record.close)
        self.addCleanup(self.tmp.cleanup)
        self.home = ConsoleService(self.record, self.root / "home", HOME)

    def console(self, node_id: str) -> ConsoleService | None:
        """A console under this spelling, or None when the constructor refuses it."""
        try:
            return ConsoleService(self.record, self.root / "other", node_id)
        except ValueError:
            return None

    def test_the_check_reads_a_node_identifier_in_exactly_one_way(self) -> None:
        """`==` on `str`, and no second reading of it. This is the whole guard.

        Asserted directly because everything else here rests on it: if the join ever
        normalised, folded or expanded an identifier, the partition would stop being
        string identity and the corpus below would stop being evidence for anything.
        """
        entries = self.record.reconstruct()
        stored = {record["node_id"] for record in authority.held(entries)}
        self.assertEqual(stored, {HOME})
        for spelling in SPELLINGS:
            with self.subTest(spelling):
                if spelling == HOME:
                    continue
                self.assertNotEqual(spelling, HOME)
                with self.assertRaises(AuthorityRefused):
                    authority.check(entries, spelling, "Bdo", "read:thread", HOME)

    def test_no_spelling_mints_a_grant_the_home_node_will_honour(self) -> None:
        """The defeating case, generalised past the three commands that found it."""
        refused_at_the_door = 0
        minted_elsewhere = 0
        for spelling in SPELLINGS:
            with self.subTest(spelling):
                other = self.console(spelling)
                if other is None:
                    refused_at_the_door += 1
                    continue
                if spelling == HOME:
                    continue
                # The spelling is a node of its own, so its office opens for whoever
                # asks first - and what it mints stays inside it.
                other.grant(MALLORY, "read:thread", HOME, granted_by=MALLORY)
                other.grant(MALLORY, "read:authority", HOME, granted_by=MALLORY)
                minted_elsewhere += 1
                entries = self.record.reconstruct()
                for capability in ("read:thread", "read:authority"):
                    with self.assertRaises(AuthorityRefused):
                        authority.check(entries, HOME, MALLORY, capability, HOME)
        self.assertGreater(refused_at_the_door, 0, "the corpus tests no malformed name")
        self.assertGreater(minted_elsewhere, 0, "the corpus tests no admitted name")

    def test_the_grant_reader_narrows_to_the_node_that_minted_them(self) -> None:
        """`authority.held`'s node filter, which nothing drove until now.

        It is the only guard of the nineteen in this service that a witness could
        neutralise on 2026-08-25 and leave the whole suite green. Two things read it:
        `console.list-grants`, which would otherwise show a caller every grant every
        node on the journal ever issued, and `permits._other_holders`, which computes
        the last-issuer rule - so an unfiltered read would count another node's
        `grant:authority` as this node's successor and let the office be emptied.
        """
        evil = ConsoleService(self.record, self.root / "evil", EVIL)
        evil.grant(MALLORY, "grant:authority", HOME, granted_by=MALLORY)
        entries = self.record.reconstruct()

        everything = {record["grant_id"] for record in authority.held(entries)}
        home_only = {record["grant_id"] for record in authority.held(entries, None, HOME)}
        evil_only = {record["grant_id"] for record in authority.held(entries, None, EVIL)}
        self.assertTrue(evil_only)
        self.assertEqual(home_only & evil_only, set())
        self.assertEqual(home_only | evil_only, everything)
        self.assertTrue(all(record["node_id"] == HOME
                            for record in authority.held(entries, None, HOME)))

    def test_another_nodes_issuer_does_not_count_as_this_nodes_successor(self) -> None:
        """The consequence of the filter above, at the rule that depends on it.

        A `grant:authority` scoped to this node but minted by another office admits
        nothing here. Counting it would let this node's only real issuer be withdrawn.
        """
        evil = ConsoleService(self.record, self.root / "evil", EVIL)
        evil.grant(MALLORY, "grant:authority", HOME, granted_by=MALLORY)
        root = [record["grant_id"] for record
                in authority.held(self.record.reconstruct(), None, HOME)
                if record["capability"] == "grant:authority"]
        self.assertEqual(len(root), 1)
        with self.assertRaises(LastIssuerStanding):
            self.home.revoke(root[0], revoked_by="Bdo")

    def test_a_grant_minted_by_the_home_node_does_admit_on_the_home_node(self) -> None:
        """The check that stops the case above passing because everything refuses."""
        self.assertTrue(
            authority.check(self.record.reconstruct(), HOME, "Bdo", "read:thread", HOME))

    def test_asserting_an_open_nodes_name_meets_the_grant_it_does_not_hold(self) -> None:
        """The bootstrap, not the field, is what stops the name being taken.

        `node_id` on a grant records which namespace minted it; nothing attests that
        the namespace was entitled to the name. What an attacker meets when it claims
        an existing node is that node's office, already open and held by somebody else.
        """
        impostor = ConsoleService(self.record, self.root / "impostor", HOME)
        self.assertEqual(authority.root_issuer(self.record.reconstruct(), HOME), "Bdo")
        with self.assertRaises(AuthorityRefused):
            impostor.grant(MALLORY, "read:thread", HOME, granted_by=MALLORY)

    def test_a_revocation_from_another_node_does_not_kill_this_nodes_grant(self) -> None:
        """The fold has to read the node too, not only the grant id.

        `permits.withdraw` refuses to withdraw another node's grant, so this cannot
        be reached through the transition - it is reached by a revocation record
        arriving in the journal, which is what a crossing does. `revocation_payload`
        records the withdrawing node for exactly this reason and `live_grants` matched
        on `grant_id` alone, so a `node:peer` revocation killed a `node:local` grant
        and undid the transition guard from the other side.
        """
        live = authority.held(self.record.reconstruct(), None, HOME)
        target = next(record for record in live
                      if record["capability"] == "read:thread")
        forged = [{"payload": {"record_kind": authority.REVOCATION_KIND,
                               "grant_id": target["grant_id"], "node_id": EVIL,
                               "revoked_by": MALLORY, "standing": "RECORDED"}}]
        entries = self.record.reconstruct() + forged
        self.assertIn(target["grant_id"], authority.live_grants(entries))
        self.assertTrue(authority.check(entries, HOME, "Bdo", "read:thread", HOME))

        # Its own office still withdraws it, which is the other half.
        owned = [{"payload": dict(forged[0]["payload"], node_id=HOME)}]
        self.assertNotIn(target["grant_id"],
                         authority.live_grants(self.record.reconstruct() + owned))

    def test_a_node_identifier_with_a_trailing_newline_is_refused(self) -> None:
        """`fullmatch`, not `match`: `$` also matches before a trailing newline.

        Such a name reached no other node's grants - `authority.check` compares byte
        for byte - but it printed identically to the real one in every report, so two
        nodes were indistinguishable by eye. Only the source-digest checks noticed the
        regex, and a digest says a byte changed, not what it cost.
        """
        for spelling in (HOME + chr(10), HOME + chr(13), HOME + " "):
            with self.subTest(repr(spelling)):
                with self.assertRaises(ValueError):
                    ConsoleService(self.record, self.root / "bad", spelling)
        self.assertTrue(ConsoleService(self.record, self.root / "good", HOME))

    def test_another_node_cannot_revoke_this_nodes_grants(self) -> None:
        """The denial of service that mirrors the minting bypass.

        A console under any other name can open its own office by bootstrap. If a
        revocation were not bound to the node too, it could then counter this node's
        root grant, and grant issue here would be over for good.
        """
        root = [record["grant_id"] for record
                in authority.held(self.record.reconstruct(), node_id=HOME)
                if record["capability"] == "grant:authority"]
        self.assertEqual(len(root), 1)
        evil = ConsoleService(self.record, self.root / "evil", EVIL)
        evil.grant(MALLORY, "read:thread", "anything", granted_by=MALLORY)
        # Answered as missing, not as another node's: the node check runs before the
        # authority check, so telling the two apart would let a caller holding nothing
        # sweep grant ids for existence and for which office issued them.
        with self.assertRaises(UnknownRecord):
            evil.revoke(root[0], revoked_by=MALLORY)
        with self.assertRaises(UnknownRecord):
            evil.revoke("grant_0000000000000000", revoked_by=MALLORY)
        # The grant that was aimed at, not merely some grant: the home node can still
        # issue, which is the thing revoking its `grant:authority` would have ended.
        self.assertEqual(
            authority.root_issuer(self.record.reconstruct(), HOME), "Bdo")
        self.assertTrue(self.home.grant("Bdo", "read:thread", "another-thread", "Bdo"))

    def test_a_node_revokes_its_own_grants_normally(self) -> None:
        """The positive half of the foreign-record check.

        Without it a lookup that returned the wrong grant record would still refuse
        every foreign revocation, for the wrong reason, and read as working.
        """
        evil = ConsoleService(self.record, self.root / "evil", EVIL)
        issued = evil.grant(MALLORY, "read:thread", "its-own", granted_by=MALLORY)
        self.assertTrue(
            authority.check(self.record.reconstruct(), EVIL, MALLORY, "read:thread",
                            "its-own"))
        evil.revoke(issued["grant_id"], revoked_by=MALLORY)
        with self.assertRaises(AuthorityRefused):
            authority.check(self.record.reconstruct(), EVIL, MALLORY, "read:thread",
                            "its-own")

    def test_holding_revoke_authority_is_not_holding_the_office(self) -> None:
        """`root_issuer` asks who took `grant:authority`, not who holds something here.

        Genesis writes the two permits-office grants together, so on a real journal
        either capability would answer with the same issuer and the distinction never
        shows. It matters anyway: the office is the right to issue, and a journal that
        carried only the withdrawal right would have an office nobody has opened.
        """
        entries = [{"payload": {"record_kind": authority.GRANT_KIND,
                                "grant_id": "grant_revoker", "node_id": HOME,
                                "operator_id": MALLORY,
                                "capability": authority.REVOKE_CAPABILITY,
                                "scope": HOME, "granted_by": MALLORY,
                                "standing": "RECORDED"}}]
        self.assertIsNone(authority.root_issuer(entries, HOME))

    def test_a_grant_recorded_before_this_field_existed_matches_no_node(self) -> None:
        """An older store's grants are not honoured under a name they never named."""
        legacy = [{"payload": {"record_kind": authority.GRANT_KIND,
                               "grant_id": "grant_legacy", "operator_id": MALLORY,
                               "capability": "read:thread", "scope": HOME,
                               "granted_by": MALLORY, "standing": "RECORDED"}}]
        with self.assertRaises(AuthorityRefused):
            authority.check(legacy, HOME, MALLORY, "read:thread", HOME)


class RecordsAreBoundToTheirNode(unittest.TestCase):
    """Binding the permit was half of it. The records had to be bound too.

    The permits office bootstraps per node *name*, and names are unbounded, so a
    caller refused `node:local`'s office opens its own and spends a grant it issued
    itself against `node:local`'s data. Every operation authorized against
    `console.node_id` and then read or wrote the whole replayed journal with no node
    filter, so the grant check passed and the read returned another node's records.

    The write case is worse than the read case: a post carried no node at all, so
    once written it could not be told from one the owner wrote.
    """

    #: Built once and copied per test. Twenty-odd records at `synchronous=FULL` is
    #: an fsync each, and rebuilding this eight times took the console suite from
    #: four seconds to ten. `OperatorContinuity` solved the same problem the same
    #: way; copying keeps every test fully isolated and only stops paying twice.
    @classmethod
    def setUpClass(cls) -> None:
        cls._template = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls._template.name) / "fixture"
        record = RecordService(root / "journal")
        home = ConsoleService(record, root / "home", HOME)
        for capability, scope in (("open:channel", "work"), ("open:session", "Bdo")):
            home.grant("Bdo", capability, scope, "Bdo")
        channel = home.open_channel("Bdo", "work", "work")
        home.grant("Bdo", "open:thread", channel["channel_id"], "Bdo")
        thread = home.open_thread("Bdo", channel["channel_id"], "home work")
        session = home.open_session("Bdo", "HUMAN", "cli")
        home.grant("Bdo", "post:message", thread["thread_id"], "Bdo")
        home.post("Bdo", session["session_id"], thread["thread_id"],
                  b"the home node's own work")
        # What the home node holds over its own records, so the cases below can tell
        # a refusal about the node from a refusal about the permit.
        home.grant("Bdo", "read:thread", thread["thread_id"], "Bdo")
        home.grant("Bdo", "read:thread", HOME, "Bdo")
        home.grant("Bdo", "read:session", "Bdo", "Bdo")
        # A cursor, and then a turn Bdo has not seen. Without a post somebody else
        # wrote, `unseen_posts` is empty whether or not the node filter is there:
        # the subject's own posts are excluded anyway, so the assertion would pass
        # for the wrong reason and the filter would go untested.
        home.grant("Bdo", "close:session", "Bdo", "Bdo")
        read_position = home.open_session("Bdo", "HUMAN", "cli")
        home.close_session("Bdo", read_position["session_id"])
        home.grant("sov", "open:session", "sov", "Bdo")
        home.grant("sov", "post:message", thread["thread_id"], "Bdo")
        away = home.open_session("sov", "MODEL", "model-binding")
        home.post("sov", away["session_id"], thread["thread_id"],
                  b"landed while Bdo was away")
        # The attacker's own office, opened under a name nobody refused it.
        evil = ConsoleService(record, root / "evil", EVIL)
        for capability in ("read:thread", "read:session", "read:authority"):
            evil.grant(MALLORY, capability, EVIL, granted_by=MALLORY)
        evil.grant(MALLORY, "read:thread", thread["thread_id"], granted_by=MALLORY)
        evil.grant(MALLORY, "open:session", MALLORY, granted_by=MALLORY)
        evil.grant(MALLORY, "post:message", thread["thread_id"], granted_by=MALLORY)
        record.close()
        cls.template_root = root
        cls.prepared_thread = thread
        cls.prepared_session = session

    @classmethod
    def tearDownClass(cls) -> None:
        cls._template.cleanup()

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self.tmp.name) / "fixture"
        shutil.copytree(self.template_root, self.root)
        self.record = RecordService(self.root / "journal")
        self.addCleanup(self.record.close)
        self.addCleanup(self.tmp.cleanup)
        self.home = ConsoleService(self.record, self.root / "home", HOME)
        self.evil = ConsoleService(self.record, self.root / "evil", EVIL)
        self.thread = self.prepared_thread
        self.session = self.prepared_session

    def test_the_publication_list_does_not_hand_over_another_nodes_threads(self) -> None:
        """The first step of the chain: this is where the thread id came from."""
        self.home.grant("Bdo", "publish:thread", self.thread["thread_id"], "Bdo")
        self.home.publish_thread("Bdo", self.thread["thread_id"])
        self.assertEqual(
            [row["thread_id"] for row
             in published_threads(self.home, operator_id="Bdo")["published"]],
            [self.thread["thread_id"]])
        seen = published_threads(self.evil, operator_id=MALLORY)
        self.assertEqual(seen["published"], [])
        self.assertEqual(seen["node_id"], EVIL)

    def test_reading_another_nodes_thread_is_refused(self) -> None:
        """The post bytes were the payload of the chain."""
        with self.assertRaises(KeyError):
            read_thread(self.evil, self.thread["thread_id"], operator_id=MALLORY)

    def test_session_context_does_not_hand_over_another_nodes_sessions(self) -> None:
        """It handed over Bdo's session id, binding, open thread titles and unread work.

        The home reading is asserted first and on purpose. There is a post by `sov`
        after Bdo's read cursor, so this node genuinely has something to hand over;
        an empty answer from the other node is then the filter working rather than
        the fixture being empty.
        """
        mine = session_context(self.home, "Bdo")
        self.assertEqual([post["actor_id"] for post in mine["unseen_posts"]], ["sov"])
        self.assertTrue(mine["prior_sessions"])
        self.assertEqual([t["thread_id"] for t in mine["open_threads"]],
                         [self.thread["thread_id"]])

        self.evil.grant(MALLORY, "read:session", "Bdo", granted_by=MALLORY)
        seen = session_context(self.evil, MALLORY, "Bdo")
        self.assertEqual(seen["prior_sessions"], [])
        self.assertEqual(seen["open_threads"], [])
        self.assertEqual(seen["unseen_posts"], [],
                         "another node read the posts that landed while Bdo was away")

    def test_posting_into_another_nodes_thread_is_refused(self) -> None:
        """The write half, and the reason it is worse than the read half."""
        mallory = self.evil.open_session(MALLORY, "MODEL", "cli")
        with self.assertRaises(ForeignNodeRecord) as refused:
            self.evil.post(MALLORY, mallory["session_id"], self.thread["thread_id"],
                           b"signed by nobody")
        self.assertEqual(refused.exception.reason_code, "FOREIGN_NODE_RECORD")
        seen = read_thread(self.home, self.thread["thread_id"], operator_id="Bdo")
        # The thread's two legitimate turns, and nothing Mallory wrote.
        self.assertEqual([post["actor_id"] for post in seen["posts"]], ["Bdo", "sov"])
        self.assertNotIn(MALLORY, {post["actor_id"] for post in seen["posts"]})

    def test_a_post_carries_the_node_that_wrote_it(self) -> None:
        """Without this the write case is undetectable after the fact."""
        posted = [entry["payload"] for entry in self.record.reconstruct()
                  if entry["payload"].get("record_kind") == "post"]
        self.assertTrue(posted)
        self.assertTrue(all(record["node_id"] == HOME for record in posted))

    def test_opening_a_thread_in_another_nodes_channel_is_refused(self) -> None:
        """`channel_exists` was declared and the channel id was taken on trust."""
        channel = self.home.open_channel("Bdo", "second", "work")
        self.evil.grant(MALLORY, "open:thread", channel["channel_id"],
                        granted_by=MALLORY)
        with self.assertRaises(ForeignNodeRecord):
            self.evil.open_thread(MALLORY, channel["channel_id"], "not yours")

    def test_closing_another_nodes_session_is_refused(self) -> None:
        """Refused, and indistinguishable from closing a session that never existed.

        `close-session` reads the session to find the operator its grant is scoped to,
        so the read precedes the authority check.
        """
        self.evil.grant(MALLORY, "close:session", "Bdo", granted_by=MALLORY)
        with self.assertRaises(UnknownRecord) as foreign:
            self.evil.close_session(MALLORY, self.session["session_id"])
        with self.assertRaises(UnknownRecord) as missing:
            self.evil.close_session(MALLORY, "session_0000000000000000")
        self.assertEqual(type(foreign.exception), type(missing.exception))
        self.assertNotIn(HOME, str(foreign.exception))

    def test_the_detector_fires_on_a_real_journal_not_only_on_a_hand_built_dict(self):
        """`foreign_records` over `records`, both driven the way production drives them.

        Every other case for this detector hands it a dict assembled in the test. That
        cannot catch the failure it actually had: `records` was narrowed to one node on
        2026-08-25, so the detector read a projection that could not contain a foreign
        record and was unconditionally empty in every production path. A verifier and
        a filter on its input went in as one change.
        """
        # A record the other node legitimately owns. One journal carrying two nodes'
        # records is the expected shape once a crossing exists (decisions/0039); what
        # must never happen is one being presented as this node's own.
        self.evil.open_session(MALLORY, "MODEL", "cli")
        projected = contract.records(self.record.reconstruct())
        named = contract.foreign_records(projected, HOME)
        self.assertTrue(named, "the detector found nothing in a two-node journal")
        self.assertTrue(any(line.startswith("operator session") for line in named), named)
        self.assertTrue(all(EVIL in line for line in named), named)

        # And the narrowed view a reader gets is clean, which is the other half:
        # filtering is a caller's job, not the projection's.
        local = contract.local_records(projected, HOME)
        self.assertEqual(contract.foreign_records(local, HOME), [])
        self.assertTrue(local["posts"])

    def test_a_view_names_the_records_it_could_not_show(self) -> None:
        """`continuity.py` promises a view names its omissions; the filter could drop.

        A record this node may not show - a peer's, or one written before console
        records carried a node and so belonging to none - is filtered out of every
        fold. Filtering it silently is the same class of defect as showing it: the
        reader is told a complete answer that is not one.
        """
        self.evil.open_session(MALLORY, "MODEL", "cli")
        read = read_thread(self.home, self.thread["thread_id"], operator_id="Bdo")
        self.assertTrue(read["posts"])
        self.assertTrue(any("omitted" in line for line in read["omissions"]),
                        read["omissions"])
        self.assertTrue(any("operator-session" in line for line in read["omissions"]),
                        read["omissions"])

        resumed = session_context(self.home, "Bdo")
        self.assertTrue(any(item["source"] == "node_scope"
                            for item in resumed["omissions"]), resumed["omissions"])

    def test_a_view_with_nothing_to_omit_says_nothing(self) -> None:
        """The other half: an omission list that always spoke would say nothing."""
        read = read_thread(self.home, self.thread["thread_id"], operator_id="Bdo")
        self.assertEqual(read["omissions"], [])

    def test_the_home_node_is_unaffected_by_any_of_it(self) -> None:
        """The check that stops the cases above passing because everything refuses."""
        self.assertTrue(read_thread(self.home, self.thread["thread_id"],
                                    operator_id="Bdo")["posts"])
        self.home.grant("Bdo", "close:session", "Bdo", "Bdo")
        self.assertEqual(
            self.home.close_session("Bdo", self.session["session_id"])["lifecycle"],
            "CLOSED")


class ReproducedThroughTheCLI(unittest.TestCase):
    """The witness's three commands, in order, against one store."""

    def cli(self, store: Path, node: str, *args: str) -> tuple[int, dict]:
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join([
            str(ROOT / "services" / "console" / "src"),
            str(ROOT / "services" / "record" / "src"),
            env.get("PYTHONPATH", ""),
        ]).rstrip(os.pathsep)
        result = subprocess.run(
            [sys.executable, "-m", "soveraeign_console_service.cli",
             "--root", str(store), "--node", node, *args],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=60)
        return result.returncode, json.loads(result.stdout or "{}")

    def test_minting_under_another_node_does_not_buy_a_read_on_this_one(self) -> None:
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "store"
            before, first = self.cli(store, HOME, "list-publications",
                                     "--operator", MALLORY)
            self.assertEqual(before, 2)
            self.assertEqual(first["reason_code"], "NO_LIVE_GRANT")

            minted, grant = self.cli(store, EVIL, "grant", "--operator", MALLORY,
                                     "--capability", "read:thread", "--scope", HOME,
                                     "--granted-by", MALLORY)
            self.assertEqual(minted, 0, "the other node's office is its own to open")
            self.assertEqual(grant["node_id"], EVIL)

            after, second = self.cli(store, HOME, "list-publications",
                                     "--operator", MALLORY)
            self.assertEqual(after, 2, "a grant minted under node:evil bought the read")
            self.assertEqual(second["reason_code"], "NO_LIVE_GRANT")

    def test_the_same_route_does_not_buy_a_post_into_another_operators_thread(self) -> None:
        """The regression half: it defeated operations that were already enforcing."""
        with TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            store = Path(tmp) / "store"
            for capability, scope in (("open:channel", "work"), ("open:session", "Bdo")):
                self.assertEqual(
                    self.cli(store, HOME, "grant", "--operator", "Bdo",
                             "--granted-by", "Bdo",
                             "--capability", capability, "--scope", scope)[0], 0)
            channel = self.cli(store, HOME, "open-channel", "--operator", "Bdo",
                               "--name", "work", "--domain", "work")[1]
            self.assertEqual(
                self.cli(store, HOME, "grant", "--operator", "Bdo",
                         "--granted-by", "Bdo", "--capability", "open:thread",
                         "--scope", channel["channel_id"])[0], 0)
            thread = self.cli(store, HOME, "open-thread", "--operator", "Bdo",
                              "--channel", channel["channel_id"], "--title", "work")[1]
            session = self.cli(store, HOME, "open-session", "--operator", "Bdo",
                               "--actor-kind", "HUMAN", "--binding", "cli")[1]

            self.assertEqual(
                self.cli(store, EVIL, "grant", "--operator", "Bdo",
                         "--capability", "post:message",
                         "--scope", thread["thread_id"],
                         "--granted-by", MALLORY)[0], 0)
            code, refusal = self.cli(store, HOME, "post", "--operator", "Bdo",
                                     "--session", session["session_id"], "--thread",
                                     thread["thread_id"], "--body", "minted elsewhere")
            self.assertEqual(code, 2)
            self.assertEqual(refusal["reason_code"], "NO_LIVE_GRANT")


if __name__ == "__main__":
    unittest.main()
