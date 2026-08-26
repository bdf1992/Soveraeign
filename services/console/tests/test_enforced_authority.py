"""Nine console operations that admitted any caller, driven from both sides.

Until 2026-08-25 nine BUILT console capabilities declared an authority in
`contracts/capability-offices.json` and checked nothing, so `console.grant` would
write a grant for whoever asked and `console.list-publications` would read the
node's outward surface for anyone who could run the command. The discovery surface
reported the fact - `NOT_ENFORCED`, named in `discovery.py` - rather than reporting
them as unanswerable, and Bdo ruled to guard all nine, having been told that a check
removes an ability from whoever can call them today.

Each of the nine is driven twice against the same fixture: once by a participant
holding nothing, which must refuse and leave the journal's record count unchanged,
and once by the same participant holding exactly the grant the office table names.
The pair is what makes it a check rather than a spelling: an operation that always
refused would pass the first case, and one that never checked would pass the second.

The refusal is asserted through the journal rather than through the exception, so a
transition that raised and wrote nothing fails here. `append.py` requires a refusal
to be as visible as a commit; a refusal leaving no trace cannot be told from an
attempt nobody made.

Passing establishes `BUILT`. It witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Callable, NamedTuple
import json
import pathlib
import shutil
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import authority  # noqa: E402
from soveraeign_console_service.continuity import (  # noqa: E402
    published_threads,
    read_thread,
    session_context,
)
from soveraeign_console_service.core import ConsoleService  # noqa: E402
from soveraeign_console_service.discovery import discover  # noqa: E402
from soveraeign_console_service.refusals import (  # noqa: E402
    AuthorityRefused,
    LastIssuerStanding,
)
from soveraeign_record_service import RecordService  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import empty_journal  # noqa: E402

MAP = json.loads((ROOT / "contracts" / "fixtures"
                  / "capability-map.reference.json").read_text("utf-8"))
OFFICES = json.loads((ROOT / "contracts"
                      / "capability-offices.json").read_text("utf-8"))["assignments"]
NODE = "node:local"
ROOT_SEAT = "Bdo"
STRANGER = "stranger"


def receipt_text(receipt: dict[str, Any]) -> str:
    """Everything a refusal receipt says in words, for asserting what it must not.

    A receipt carries the refusal message into the journal, so blunting the exception
    and leaving the receipt verbose would move the disclosure rather than close it.
    """
    return json.dumps(receipt.get("detail", {}), sort_keys=True)


class Guarded(NamedTuple):
    """One capability, how to attempt it, and the exact grant that admits it."""

    capability_id: str
    attempt: Callable[["EnforcedAuthorityTest", str], Any]
    scope: Callable[["EnforcedAuthorityTest"], str]
    #: Which of `authority.ENFORCED_SCOPE`'s subjects the scope above is. Declared
    #: per case so the table in `authority.py` is checked against what the call
    #: sites actually pass rather than only against its own key set.
    subject: str


#: Every enforced capability, named by its id so a reader can join this table to
#: `contracts/capability-offices.json` and to `authority.ENFORCED_AUTHORITY` by eye.
#:
#: All fifteen, not the nine this work guarded. Subtracting the six that already
#: enforced left them graded by nothing: `console.withdraw-publication` could have
#: its `authorize` call deleted outright and the whole gate stayed green, because its
#: only two cases were positive ones. A coverage set that excludes what it does not
#: expect to break is not a coverage set.
GUARDED = (
    Guarded("console.grant",
            lambda t, actor: t.console.grant("someone", "post:message", "thread",
                                             granted_by=actor),
            lambda t: NODE, "NODE"),
    Guarded("console.revoke",
            lambda t, actor: t.console.revoke(t.spare_grant, revoked_by=actor),
            lambda t: NODE, "NODE"),
    Guarded("console.list-grants",
            lambda t, actor: t.console.grants(reader_id=actor),
            lambda t: NODE, "NODE"),
    Guarded("console.open-session",
            lambda t, actor: t.console.open_session(actor, "HUMAN", "cli"),
            lambda t: STRANGER, "OPERATOR"),
    # The stranger closes the root seat's session, so the scope is the session's
    # owner and not the caller. A case where the two were the same could not tell
    # a check of the caller from a check of the subject.
    Guarded("console.close-session",
            lambda t, actor: t.console.close_session(actor, t.session),
            lambda t: ROOT_SEAT, "OPERATOR"),
    Guarded("console.discover-operations",
            lambda t, actor: discover(t.console, MAP, actor),
            lambda t: STRANGER, "OPERATOR"),
    # Likewise: the stranger reads the root seat's continuity, not its own.
    Guarded("console.session-context",
            lambda t, actor: session_context(t.console, actor, ROOT_SEAT),
            lambda t: ROOT_SEAT, "OPERATOR"),
    Guarded("console.read-thread",
            lambda t, actor: read_thread(t.console, t.thread, operator_id=actor),
            lambda t: None, "THREAD"),
    Guarded("console.list-publications",
            lambda t, actor: published_threads(t.console, operator_id=actor),
            lambda t: NODE, "NODE"),
    # The six that already enforced before 2026-08-25. Each mutates a subject of its
    # own so table order cannot make one case depend on another having run.
    Guarded("console.open-channel",
            lambda t, actor: t.console.open_channel(actor, "ops", "governance"),
            lambda t: "governance", "DOMAIN"),
    Guarded("console.open-thread",
            lambda t, actor: t.console.open_thread(actor, t.channel, "another"),
            lambda t: t.channel, "CHANNEL"),
    Guarded("console.archive-thread",
            lambda t, actor: t.console.archive_thread(actor, t.archivable),
            lambda t: t.channel, "CHANNEL"),
    Guarded("console.publish-thread",
            lambda t, actor: t.console.publish_thread(actor, t.thread),
            lambda t: None, "THREAD"),
    Guarded("console.withdraw-publication",
            lambda t, actor: t.console.withdraw_publication(actor, t.publication),
            lambda t: None, "THREAD"),
    Guarded("console.post",
            lambda t, actor: t.console.post(actor, t.outsider, t.thread, b"guarded"),
            lambda t: None, "THREAD"),
)


class EnforcedAuthorityTest(unittest.TestCase):
    """One fixture, driven nine times without a grant and nine times with one."""

    #: Built once and copied per test. Every record costs an fsync at
    #: `synchronous=FULL`, and rebuilding these nine across every case is what took
    #: this module past a second. `OperatorContinuity` established the pattern;
    #: copying keeps each test fully isolated and only stops paying twice.
    @classmethod
    def setUpClass(cls) -> None:
        cls._template = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(cls._template.name) / "fixture"
        record = RecordService(root / "journal")
        console = ConsoleService(record, root / "console", NODE)
        # The root seat's own setup. Its first grant records it as this node's root
        # issuer, which is what lets it issue the rest (`authority.py`, Bootstrap).
        for capability, scope in (("open:channel", "governance"),
                                  ("open:session", ROOT_SEAT)):
            console.grant(ROOT_SEAT, capability, scope)
        channel = console.open_channel(ROOT_SEAT, "governance", "governance")
        console.grant(ROOT_SEAT, "open:thread", channel["channel_id"])
        thread = console.open_thread(ROOT_SEAT, channel["channel_id"], "guarded")
        session = console.open_session(ROOT_SEAT, "HUMAN", "cli")
        # Something for `console.revoke` to aim at that no case depends on.
        spare = console.grant("someone", "post:message", thread["thread_id"])
        # A separate thread for `archive-thread` to close, so archiving it does not
        # take the thread `post` and `publish-thread` need out from under them: the
        # cases below share one journal per test method and run in table order.
        archivable = console.open_thread(ROOT_SEAT, channel["channel_id"], "closes")
        # A mark for `withdraw-publication` to withdraw, and the stranger's own
        # session, because `post` refuses a session it does not own before any grant
        # can help it (`posts.py`, ACTOR_ATTRIBUTION_MISMATCH).
        console.grant(ROOT_SEAT, "publish:thread", thread["thread_id"])
        mark = console.publish_thread(ROOT_SEAT, thread["thread_id"])
        opening = console.grant(STRANGER, "open:session", STRANGER)
        outsider = console.open_session(STRANGER, "MODEL", "cli")
        # Withdrawn again: the stranger must own a session for `post` to reach its
        # attribution check, and must still hold nothing at all when the cases start,
        # or `console.open-session` would have no defeating case left.
        console.revoke(opening["grant_id"])
        record.close()
        cls.template_root = root
        cls.prepared_channel = channel["channel_id"]
        cls.prepared_thread = thread["thread_id"]
        cls.prepared_archivable = archivable["thread_id"]
        cls.prepared_publication = mark["publication_id"]
        cls.prepared_session = session["session_id"]
        cls.prepared_outsider = outsider["session_id"]
        cls.prepared_spare = spare["grant_id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls._template.cleanup()

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.tmp.name) / "fixture"
        shutil.copytree(self.template_root, root)
        self.record = RecordService(root / "journal")
        self.addCleanup(self.record.close)
        self.addCleanup(self.tmp.cleanup)
        self.console = ConsoleService(self.record, root / "console", NODE)
        self.channel = self.prepared_channel
        self.thread = self.prepared_thread
        self.archivable = self.prepared_archivable
        self.publication = self.prepared_publication
        self.session = self.prepared_session
        self.outsider = self.prepared_outsider
        self.spare_grant = self.prepared_spare

    def scope(self, case: Guarded) -> str:
        """The exact scope this case's grant must carry; `None` means the thread."""
        return case.scope(self) or self.thread

    def subject_values(self) -> dict[str, str]:
        """What each declared subject in `authority.ENFORCED_SCOPE` resolves to here."""
        return {"NODE": NODE, "THREAD": self.thread, "CHANNEL": self.channel,
                "DOMAIN": "governance"}

    def records(self) -> int:
        return sum(1 for entry in self.record.entries() if entry["kind"] == "EVENT")

    def last_receipt(self) -> dict[str, Any]:
        receipts = [entry for entry in self.record.entries() if entry["kind"] == "RECEIPT"]
        return receipts[-1]["payload"]

    def test_the_table_here_names_every_enforced_capability(self) -> None:
        """A capability enforced but ungraded must land here rather than pass quietly.

        This subtracted the six that already enforced, which made them ungraded by
        construction - `console.withdraw-publication` could be fully unguarded with
        the whole gate green. Nothing is subtracted now, so adding an entry to
        `ENFORCED_AUTHORITY` without a case here fails.
        """
        self.assertEqual({case.capability_id for case in GUARDED},
                         set(authority.ENFORCED_AUTHORITY))

    def test_the_table_here_covers_every_built_console_capability(self) -> None:
        """The census that has to reach call sites, joined where the driving happens.

        `test_discovery.py` asserts the same coverage out of `ENFORCED_AUTHORITY` and
        the capability map, and both are declarations - it passes unchanged if every
        call site stops checking. This is the same join made against the table above,
        every entry of which is driven ungranted, granted, at the wrong scope and
        after revocation. A BUILT console capability that gains no case here fails.
        """
        built = {row["capability_id"] for row in MAP["capabilities"]
                 if row["service_id"] == "console" and row["service_standing"] == "BUILT"}
        self.assertEqual({case.capability_id for case in GUARDED}, built)

    def test_each_refuses_a_participant_holding_nothing(self) -> None:
        """The defeating case: the operation must not run for an ungranted caller."""
        for case in GUARDED:
            with self.subTest(case.capability_id):
                before = self.records()
                with self.assertRaises(AuthorityRefused) as raised:
                    case.attempt(self, STRANGER)
                required = OFFICES[case.capability_id]["required_authority"]
                # Asserted off the exception, not out of the message. The capability
                # and the scope have to be exactly right, which is what makes this a
                # check rather than a substring that any refusal would satisfy - and
                # the scope must not appear in the text a caller is handed, because a
                # scope is an operator id, a channel or a thread. `close-session`
                # answered "no live close:session grant scoped to Bdo" to anybody.
                receipt = self.last_receipt()
                self.assertEqual(raised.exception.capability, required)
                self.assertEqual(raised.exception.scope, self.scope(case))
                self.assertEqual(
                    str(raised.exception),
                    f"{STRANGER} holds no live {required} grant for this operation")
                if self.scope(case) != STRANGER:
                    # A scope naming something other than the caller itself: an
                    # operator, a channel, a thread, the node. None of those may
                    # reach a caller that holds nothing. Where the scope is the
                    # caller's own id it is already its own, and the message names
                    # it as the actor rather than as the thing it missed.
                    self.assertNotIn(self.scope(case), str(raised.exception))
                    self.assertNotIn(self.scope(case), receipt_text(receipt))
                self.assertEqual(receipt["outcome"], "REFUSED")
                self.assertEqual(receipt["event"], case.capability_id)
                self.assertEqual(receipt["detail"]["reason_code"], "NO_LIVE_GRANT")
                self.assertEqual(self.records(), before,
                                 "a refused operation wrote a record")

    def test_each_admits_the_same_participant_holding_the_declared_grant(self) -> None:
        """The positive case: the exact grant the office table names is enough."""
        for case in GUARDED:
            with self.subTest(case.capability_id):
                required = OFFICES[case.capability_id]["required_authority"]
                self.console.grant(STRANGER, required, self.scope(case))
                self.assertIsNotNone(case.attempt(self, STRANGER))

    def test_a_grant_of_the_right_name_at_the_wrong_scope_does_not_admit(self) -> None:
        """A scope is part of the grant, not decoration on it."""
        for case in GUARDED:
            with self.subTest(case.capability_id):
                required = OFFICES[case.capability_id]["required_authority"]
                self.console.grant(STRANGER, required, "somewhere-else")
                with self.assertRaises(AuthorityRefused):
                    case.attempt(self, STRANGER)

    def test_a_revoked_grant_stops_admitting_the_next_attempt(self) -> None:
        """Enforcement that survived revocation would be a permanent credential."""
        for case in GUARDED:
            with self.subTest(case.capability_id):
                required = OFFICES[case.capability_id]["required_authority"]
                issued = self.console.grant(STRANGER, required, self.scope(case))
                self.console.revoke(issued["grant_id"])
                with self.assertRaises(AuthorityRefused):
                    case.attempt(self, STRANGER)

    def test_every_enforced_capability_declares_what_its_scope_names(self) -> None:
        """`ENFORCED_SCOPE` is checked against the scope the call site really passes.

        A table nothing reads is a comment. This resolves each declared subject to
        the value this fixture would have to grant, and fails if a call site's scope
        stops matching what `authority.py` says that capability scopes to.
        """
        self.assertEqual(set(authority.ENFORCED_SCOPE),
                         set(authority.ENFORCED_AUTHORITY))
        resolved = self.subject_values()
        for case in GUARDED:
            with self.subTest(case.capability_id):
                declared = authority.ENFORCED_SCOPE[case.capability_id]
                self.assertEqual(declared, case.subject)
                if declared == "OPERATOR":
                    self.assertNotIn(self.scope(case), set(resolved.values()))
                else:
                    self.assertEqual(self.scope(case), resolved[declared])

    def test_reading_another_operators_continuity_checks_the_reader(self) -> None:
        """A check made against the subject is not a check.

        Every operator holds `read:session` over itself, because that is what its
        own continuity read costs. If `session-context` fell back to the subject when
        no reader was named, naming any operator would admit any caller. It refused
        for the stranger above; here the root seat, which does hold the grant over
        itself, still cannot be used as a stand-in for the caller.
        """
        self.console.grant(ROOT_SEAT, "read:session", ROOT_SEAT)
        with self.assertRaises(AuthorityRefused):
            session_context(self.console, STRANGER, ROOT_SEAT)
        self.assertIsNotNone(session_context(self.console, ROOT_SEAT))

    def test_a_close_by_somebody_else_is_attributed_to_who_closed_it(self) -> None:
        """The record must not read as the owner having closed their own session.

        `AGENTS.md`: every consequential decision emits an event naming the actor.
        A close carrying the owner's name would put an act in the owner's history
        that the owner did not perform.
        """
        self.console.grant(STRANGER, "close:session", ROOT_SEAT)
        closed = self.console.close_session(STRANGER, self.session)
        self.assertEqual(closed["operator_id"], ROOT_SEAT)
        entries = [entry for entry in self.record.entries()
                   if entry["payload"].get("record_kind") == "operator-session-lifecycle"]
        self.assertEqual(entries[-1]["actor"], STRANGER)
        receipt = [entry for entry in self.record.entries()
                   if entry["kind"] == "RECEIPT"][-1]
        self.assertEqual(receipt["payload"]["event"], "console.close-session")
        self.assertEqual(receipt["actor"], STRANGER)


class RootIssuerTest(unittest.TestCase):
    """The bootstrap `console.grant` needs, and the ways it must not become a hole."""

    def setUp(self) -> None:
        self.tmp = TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self.tmp.name)
        self.record = RecordService(empty_journal(root / "journal"))
        self.addCleanup(self.record.close)
        self.addCleanup(self.tmp.cleanup)
        self.console = ConsoleService(self.record, root / "console", NODE)

    def test_a_journal_with_no_grant_has_no_root_issuer_yet(self) -> None:
        self.assertIsNone(authority.root_issuer(self.record.reconstruct(), NODE))

    def test_the_first_issuer_becomes_the_root_and_the_record_says_so(self) -> None:
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        self.assertEqual(authority.root_issuer(self.record.reconstruct(), NODE), "founder")
        origin = {(record["operator_id"], record["capability"], record["scope"])
                  for record in authority.held(self.record.reconstruct())
                  if record["granted_by"] == record["operator_id"]}
        self.assertEqual(origin, {("founder", "grant:authority", NODE),
                                  ("founder", "revoke:authority", NODE)})

    def test_a_second_issuer_is_refused_rather_than_bootstrapping_again(self) -> None:
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        with self.assertRaises(AuthorityRefused):
            self.console.grant("mallory", "grant:authority", NODE, granted_by="mallory")

    def issuers(self, capability: str = "grant:authority") -> list[str]:
        """Live grants of an office capability that can actually still spend it.

        Scoped to the node, because that is what `permits.issue` and
        `permits.withdraw` require. A grant of the same name at another scope admits
        nothing and is not an issuer.
        """
        return [record["grant_id"] for record
                in authority.held(self.record.reconstruct(), None, NODE)
                if record["capability"] == capability and record["scope"] == NODE]

    def test_the_nodes_last_issuer_cannot_be_withdrawn(self) -> None:
        """An operator must not be able to brick its own permits office by accident.

        Revocation appends and the bootstrap is once-ever, so withdrawing the last
        live `grant:authority` used to end grant issue on the node for good, with no
        console operation able to restore it.
        """
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        only = self.issuers()
        self.assertEqual(len(only), 1)
        with self.assertRaises(LastIssuerStanding) as refused:
            self.console.revoke(only[0], revoked_by="founder")
        self.assertEqual(refused.exception.reason_code, "MISSING_PRECONDITION")
        self.assertEqual(self.issuers(), only, "the office lost its issuer anyway")
        # The office still works, which is the whole point of refusing.
        self.assertTrue(self.console.grant("reader", "post:message", "t",
                                           granted_by="founder"))

    def test_a_successor_at_the_wrong_scope_does_not_hold_the_office(self) -> None:
        """The defeating case for the guard itself: a name is not a successor.

        `issue` requires a `grant:authority` whose scope equals the node. One
        recorded at any other scope admits nothing, so counting it as an issuer let
        the last real one be withdrawn and left the office unowned and unrecoverable -
        the exact state this rule exists to prevent, reachable by mistyping `--scope`
        during an ordinary root rotation.
        """
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        only = self.issuers()
        self.assertEqual(len(only), 1)
        self.console.grant("nobody", "grant:authority", "not-a-node",
                           granted_by="founder")
        self.assertEqual(self.issuers(), only, "a wrong-scope grant counted as an issuer")
        with self.assertRaises(LastIssuerStanding):
            self.console.revoke(only[0], revoked_by="founder")
        # The office still issues, which is what the wrong predicate destroyed.
        self.assertTrue(self.console.grant("reader", "post:message", "t",
                                           granted_by="founder"))

    def test_the_nodes_last_revoker_cannot_be_withdrawn_either(self) -> None:
        """Withdrawing it ends revocation on the node, including of a compromised grant.

        `revoke:authority` had no last-holder rule at all: the guard named one
        capability and the office runs on two.
        """
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        only = self.issuers("revoke:authority")
        self.assertEqual(len(only), 1)
        with self.assertRaises(LastIssuerStanding) as refused:
            self.console.revoke(only[0], revoked_by="founder")
        self.assertEqual(refused.exception.reason_code, "MISSING_PRECONDITION")
        self.assertEqual(self.issuers("revoke:authority"), only)
        # Revocation still works, which is what withdrawing it would have ended.
        spare = self.console.grant("reader", "post:message", "t2", granted_by="founder")
        self.assertTrue(self.console.revoke(spare["grant_id"], revoked_by="founder"))

    def test_a_grant_of_an_office_capability_at_another_scope_is_freely_withdrawn(self):
        """The rule guards the office, not every record wearing its name."""
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        aside = self.console.grant("nobody", "grant:authority", "not-a-node",
                                   granted_by="founder")
        self.assertTrue(self.console.revoke(aside["grant_id"], revoked_by="founder"))

    def test_an_issuer_is_withdrawn_once_a_successor_holds_the_office(self) -> None:
        """Refusing the last one must not make the first one permanent.

        Grant a successor, then withdraw the predecessor. This is why the rule is
        about the last issuer and not about the root grant.
        """
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        first = self.issuers()[0]
        self.console.grant("successor", "grant:authority", NODE, granted_by="founder")
        self.console.revoke(first, revoked_by="founder")
        self.assertNotIn(first, self.issuers())
        self.assertTrue(self.console.grant("reader", "post:message", "t2",
                                           granted_by="successor"))
        with self.assertRaises(AuthorityRefused):
            self.console.grant("mallory", "post:message", "t3", granted_by="founder")

    def test_withdrawing_an_issuer_does_not_reopen_the_bootstrap(self) -> None:
        """Once-ever, not once-while-live: a revocation must not provoke a second root."""
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        first = self.issuers()[0]
        self.console.grant("successor", "grant:authority", NODE, granted_by="founder")
        self.console.revoke(first, revoked_by="founder")
        self.assertEqual(authority.root_issuer(self.record.reconstruct(), NODE), "founder")
        with self.assertRaises(AuthorityRefused):
            self.console.grant("mallory", "post:message", "thread_x", granted_by="mallory")

    def test_a_second_node_on_one_journal_opens_its_own_permits_office(self) -> None:
        """The bootstrap is once per node, not once per journal.

        A journal can carry more than one console - a peer's records reach a local
        journal through a crossing. A journal-wide condition let whichever console
        issued first take a root scoped to its own node and left every other node on
        that store permanently unable to issue a first grant, which is a denial of
        service reachable from the shipped CLI through `--node`.
        """
        peer = ConsoleService(self.record, pathlib.Path(self.tmp.name) / "peer",
                              "node:peer-one")
        peer.grant("reader", "read:thread", "thread_x", granted_by="squatter")
        self.assertEqual(
            authority.root_issuer(self.record.reconstruct(), "node:peer-one"), "squatter")
        self.assertIsNone(authority.root_issuer(self.record.reconstruct(), NODE))
        # The home node opens its own office and is not blocked by the peer's.
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        self.assertEqual(authority.root_issuer(self.record.reconstruct(), NODE), "founder")
        with self.assertRaises(AuthorityRefused):
            self.console.grant("squatter", "post:message", "t", granted_by="squatter")

    def test_a_grant_scoped_to_a_node_is_not_that_nodes_office_being_open(self) -> None:
        """Who holds the node's permits office is who first took `grant:authority` over it.

        A scope is a string, so one console can mint a grant naming another node.
        Reading the root off the first record that merely mentions the node would let
        that grant stand in for the office, and the real node would then be refused
        its own first grant by an issuer that never opened it.
        """
        self.console.grant("reader", "read:thread", "thread_x", granted_by="founder")
        self.console.grant("squatter", "read:authority", "node:peer-one",
                           granted_by="founder")
        entries = self.record.reconstruct()
        self.assertIn("node:peer-one", {record["scope"] for record in authority.held(entries)})
        self.assertIsNone(authority.root_issuer(entries, "node:peer-one"))

    def test_a_grant_carries_an_address_of_the_declared_shape(self) -> None:
        """A grant id is an address: receipts name it in `authority_grant_ids`."""
        issued = self.console.grant("reader", "read:thread", "thread_x",
                                    granted_by="founder")
        self.assertRegex(issued["grant_id"], r"^grant_[0-9a-f]{16}$")

    def test_the_genesis_grants_are_ordinary_records_a_reader_can_see(self) -> None:
        """A bootstrap that hid would be a code path skipping the check, not a record."""
        self.console.grant("founder", "read:authority", NODE, granted_by="founder")
        listed = self.console.grants(reader_id="founder")
        self.assertEqual({record["capability"] for record in listed},
                         {"grant:authority", "revoke:authority", "read:authority"})
        self.assertTrue(all(record["standing"] == "RECORDED" for record in listed))


if __name__ == "__main__":
    unittest.main()
