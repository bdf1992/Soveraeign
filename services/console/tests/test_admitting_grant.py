"""Which live grant admits an operation, and what the receipt is then allowed to say.

`authority.check` returns one grant id and `append.emit` puts it on the terminal
receipt as the authority a committed operation was admitted under. That id is a
record-integrity claim about the journal, so which of several live matches is
returned has to be a decision somebody made rather than the incidental order of a
fold. It was not: `matches[-1]` could be rewritten to `matches[0]` - the opposite
rule - and every check in the repository stayed green.

Two rules are pinned here.

*The newest live match admits.* An issuer's latest decision about a capability is
the one that describes the node now. `NewestLiveGrantAdmits` fails against the
reversed rule.

*A grant cannot admit the record that withdraws it.* A revoker whose only live
`revoke:authority` was the grant being withdrawn spent that grant on its own
withdrawal, and the `COMMITTED` receipt then named, as the authority for the
operation, a grant the same operation had revoked. `RevokedGrantIsNeverCited`
reads that straight out of the journal rather than out of one call's return
value, so it catches the claim wherever it is made.

What none of this establishes, said here because the case names could be read as
saying it: the journal walk below drives one writer. A second process on the same
store can append a revocation of the admitting grant between the check and the
append, and the receipt then lands after it - reproduced on 2026-08-26 with two
ordinary processes against one `--root`, and recorded in
`services/console/KNOWN-GAPS.md`. Closing it needs a transactional read-and-append
the Record Service does not offer, so it is not a case that could be added here.

Passing establishes `BUILT`. It witnesses nothing.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
import contextlib
import sys
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))

from soveraeign_console_service import authority  # noqa: E402
from soveraeign_console_service.core import ConsoleService  # noqa: E402
from soveraeign_console_service.refusals import (  # noqa: E402
    AuthorityRefused,
    LastIssuerStanding,
)
from soveraeign_record_service import RecordService  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fixtures import empty_journal  # noqa: E402

NODE = "node:local"
FOUNDER = "founder"


def cited(entries: list[dict[str, Any]], event: str) -> list[str]:
    """Every grant id the last committed receipt for one operation names."""
    for entry in reversed(entries):
        payload = entry["payload"]
        if (entry["kind"] == "RECEIPT" and payload.get("event") == event
                and payload.get("outcome") == "COMMITTED"):
            return list(payload["detail"]["authority_grant_ids"])
    raise AssertionError(f"no committed receipt for {event}")


class ConsoleCase(unittest.TestCase):
    """One console over a private empty journal, with this node's office already open."""

    def setUp(self) -> None:
        holder = TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(holder.cleanup)
        root = Path(holder.name) / "console"
        root.mkdir(parents=True)
        self.record = RecordService(empty_journal(root / "journal"))
        self.addCleanup(self.record.close)
        self.console = ConsoleService(self.record, root, NODE)
        # The first issue opens this node's permits office and makes `founder` its
        # recorded root, which is the ordinary bootstrap and not a code path.
        self.console.grant("reader", "read:thread", "thread_x", granted_by=FOUNDER)

    def live(self, operator_id: str, capability: str, scope: str) -> list[str]:
        """Live grant ids for one operator, capability and scope, in journal order."""
        return [record["grant_id"]
                for record in authority.live_grants(self.record.reconstruct()).values()
                if record.get("node_id") == NODE
                and record["operator_id"] == operator_id
                and record["capability"] == capability
                and record["scope"] == scope]


class NewestLiveGrantAdmits(ConsoleCase):
    """The rule that `matches[0]` would reverse, driven where the two disagree."""

    def test_the_newest_of_two_live_grants_is_the_one_cited(self) -> None:
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        held = self.live("ana", "open:channel", "governance")
        self.assertEqual(len(held), 2, "the fixture needs two live matches to decide")
        self.console.open_channel("ana", "governance channel", "governance")
        self.assertEqual(cited(self.record.reconstruct(), "console.open-channel"),
                         [held[-1]],
                         "the receipt cites a grant that is not the newest live match")

    def test_a_withdrawn_newest_leaves_the_remaining_grant_admitting(self) -> None:
        """Newest means newest among the live, not newest ever recorded."""
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        held = self.live("ana", "open:channel", "governance")
        self.console.revoke(held[-1], revoked_by=FOUNDER)
        self.console.open_channel("ana", "governance channel", "governance")
        self.assertEqual(cited(self.record.reconstruct(), "console.open-channel"),
                         [held[0]])


class RevokedGrantIsNeverCited(ConsoleCase):
    """A grant may not be spent on its own withdrawal."""

    def revokers(self) -> list[str]:
        """Live `revoke:authority` grants at node scope, whoever holds them."""
        return [record["grant_id"]
                for record in authority.held(self.record.reconstruct(), None, NODE)
                if record["capability"] == authority.REVOKE_CAPABILITY
                and record["scope"] == NODE]

    def test_a_revoker_cannot_spend_the_grant_it_is_withdrawing(self) -> None:
        """`founder` holds one revoker and `deputy` holds another, so the office stands.

        The last-issuer rule is therefore satisfied and nothing else stopped the
        founder spending its own `revoke:authority` on withdrawing that same grant.
        """
        self.console.grant("deputy", authority.REVOKE_CAPABILITY, NODE,
                           granted_by=FOUNDER)
        own = self.live(FOUNDER, authority.REVOKE_CAPABILITY, NODE)
        self.assertEqual(len(own), 1, "the founder holds exactly its bootstrap revoker")
        with self.assertRaises(AuthorityRefused) as refused:
            self.console.revoke(own[0], revoked_by=FOUNDER)
        self.assertEqual(refused.exception.reason_code, "NO_LIVE_GRANT")
        self.assertIn(own[0], self.revokers(), "the grant was withdrawn anyway")

    def test_the_refusal_is_recorded_like_every_other(self) -> None:
        """`append.py`: a refusal leaving no trace cannot be told from an attempt nobody made."""
        self.console.grant("deputy", authority.REVOKE_CAPABILITY, NODE,
                           granted_by=FOUNDER)
        own = self.live(FOUNDER, authority.REVOKE_CAPABILITY, NODE)[0]
        with contextlib.suppress(AuthorityRefused):
            self.console.revoke(own, revoked_by=FOUNDER)
        refusals = [entry for entry in self.record.reconstruct()
                    if entry["kind"] == "RECEIPT"
                    and entry["payload"].get("outcome") == "REFUSED"
                    and entry["payload"].get("event") == "console.revoke"]
        self.assertEqual(len(refusals), 1)
        self.assertEqual(refusals[0]["payload"]["detail"]["reason_code"], "NO_LIVE_GRANT")

    def test_another_revoker_still_withdraws_it(self) -> None:
        """The ability is moved to a second holder, not removed from the node."""
        self.console.grant("deputy", authority.REVOKE_CAPABILITY, NODE,
                           granted_by=FOUNDER)
        own = self.live(FOUNDER, authority.REVOKE_CAPABILITY, NODE)[0]
        self.console.revoke(own, revoked_by="deputy")
        self.assertNotIn(own, self.revokers())

    def test_a_holder_with_two_revokers_withdraws_one_with_the_other(self) -> None:
        """One operator can still rotate its own revoker, holding both for a moment."""
        self.console.grant(FOUNDER, authority.REVOKE_CAPABILITY, NODE,
                           granted_by=FOUNDER)
        own = self.live(FOUNDER, authority.REVOKE_CAPABILITY, NODE)
        self.assertEqual(len(own), 2)
        self.console.revoke(own[0], revoked_by=FOUNDER)
        self.assertEqual(cited(self.record.reconstruct(), "console.revoke"), [own[1]])
        self.assertNotIn(own[0], self.revokers())

    def test_the_last_revoker_rule_still_answers_first(self) -> None:
        """Ordering, not accident: the office rule speaks before the exclusion does.

        With no second holder both rules would refuse, and the caller is owed the one
        that says what is actually wrong - the node would be left unable to revoke -
        rather than a bare `NO_LIVE_GRANT`.
        """
        own = self.live(FOUNDER, authority.REVOKE_CAPABILITY, NODE)[0]
        with self.assertRaises(LastIssuerStanding) as refused:
            self.console.revoke(own, revoked_by=FOUNDER)
        self.assertEqual(refused.exception.reason_code, "MISSING_PRECONDITION")

    def test_one_writer_never_commits_a_receipt_citing_a_grant_it_had_revoked(self):
        """The property, read out of the journal rather than out of one return value.

        Every `COMMITTED` receipt names the grants that admitted it. At the position
        that receipt occupies, each of those grants must still be live - which is what
        `authority.live_grants` decides, replayed over exactly the entries that precede
        it. The self-withdrawal above is attempted here so the walk has the record it
        was written to catch.

        One writer. A concurrent second writer on the same store defeats this and the
        console cannot stop it; the module docstring says where that is recorded.
        """
        self.console.grant("deputy", authority.REVOKE_CAPABILITY, NODE,
                           granted_by=FOUNDER)
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        self.console.open_channel("ana", "governance channel", "governance")
        own = self.live(FOUNDER, authority.REVOKE_CAPABILITY, NODE)[0]
        with contextlib.suppress(AuthorityRefused):
            self.console.revoke(own, revoked_by=FOUNDER)
        self.console.revoke(self.live("ana", "open:channel", "governance")[0],
                            revoked_by="deputy")

        entries = self.record.reconstruct()
        checked = 0
        for position, entry in enumerate(entries):
            payload = entry["payload"]
            if entry["kind"] != "RECEIPT" or payload.get("outcome") != "COMMITTED":
                continue
            live = authority.live_grants(entries[:position])
            for grant_id in payload["detail"]["authority_grant_ids"]:
                checked += 1
                self.assertIn(
                    grant_id, live,
                    f"{payload['event']} committed citing {grant_id}, which the "
                    f"journal has already revoked at entry {position}")
        self.assertGreater(checked, 0, "the walk found no cited grant to judge")


class TheFoldReadsAGrantOnce(ConsoleCase):
    """What `live_grants` does with a record `console.grant` would never have written.

    `console.grant` mints a uuid, so nothing here is reachable through it. A record
    bearing an id somebody else chose arrives by constructing the journal or through a
    crossing, which is exactly where one would come from, and the fold is what decides
    what it means. Both cases below are the fold refusing to treat a second record as an
    amendment: `RecordService` never updates an entry, so the first record bearing an id
    is the grant, and a later one repeating it is a duplicate or a forgery.
    """

    def append_grant(self, payload: dict[str, Any]) -> None:
        """Put a grant record in the journal without going through `console.grant`."""
        self.record.append("EVENT", payload["grant_id"], "someone",
                           dict(payload, record_kind=authority.GRANT_KIND))

    def test_a_second_record_reusing_an_id_does_not_rewrite_the_grant(self) -> None:
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        held = self.live("ana", "open:channel", "governance")[0]
        self.append_grant({"grant_id": held, "node_id": NODE, "operator_id": "mallory",
                           "capability": authority.GRANT_CAPABILITY, "scope": NODE,
                           "granted_by": "mallory", "granted_at": self.console.stamp(),
                           "standing": "RECORDED"})
        record = authority.live_grants(self.record.reconstruct())[held]
        self.assertEqual(record["operator_id"], "ana")
        self.assertEqual(record["capability"], "open:channel")
        with self.assertRaises(AuthorityRefused):
            self.console.grant("mallory", "post:message", "t", granted_by="mallory")

    def test_a_repeated_id_does_not_move_a_grant_in_the_append_order(self) -> None:
        """`check` selects on that order, so a record that reorders it decides admissions."""
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        first, second = self.live("ana", "open:channel", "governance")
        self.append_grant({"grant_id": first, "node_id": NODE, "operator_id": "ana",
                           "capability": "open:channel", "scope": "governance",
                           "granted_by": FOUNDER, "granted_at": self.console.stamp(),
                           "standing": "RECORDED"})
        self.console.open_channel("ana", "governance channel", "governance")
        self.assertEqual(cited(self.record.reconstruct(), "console.open-channel"),
                         [second])

    def test_a_revocation_naming_no_node_withdraws_nothing(self) -> None:
        """The mirror of a grant naming no node admitting nothing.

        Both fail in the direction that refuses. A revocation that names no office
        cannot be attributed to one, so honouring it would let an unattributable record
        end a grant - and `permits.withdraw` already refuses to withdraw across nodes.
        """
        self.console.grant("ana", "open:channel", "governance", granted_by=FOUNDER)
        held = self.live("ana", "open:channel", "governance")[0]
        self.record.append("EVENT", held, "nobody", {
            "record_kind": authority.REVOCATION_KIND, "grant_id": held,
            "revoked_by": "nobody", "revoked_at": self.console.stamp(),
            "standing": "RECORDED"})
        self.assertIn(held, authority.live_grants(self.record.reconstruct()))
        self.console.open_channel("ana", "governance channel", "governance")
        self.assertEqual(cited(self.record.reconstruct(), "console.open-channel"), [held])

    def test_a_nodeless_revocation_does_not_withdraw_a_nodeless_grant_either(self) -> None:
        """The one journal shape the node comparison alone would have let through.

        `None == None`, so a revocation carrying no node withdrew a grant carrying no
        node - two unattributable records cancelling each other. Neither could ever
        admit anything, so nothing is gained by honouring it, and the rule the fold
        states is that a record naming no office does not act as one.
        """
        payload = {"grant_id": "grant_nonodeatall00", "operator_id": "ana",
                   "capability": "open:channel", "scope": "governance",
                   "granted_by": FOUNDER, "granted_at": self.console.stamp(),
                   "standing": "RECORDED"}
        self.record.append("EVENT", payload["grant_id"], FOUNDER,
                           dict(payload, record_kind=authority.GRANT_KIND))
        self.record.append("EVENT", payload["grant_id"], "nobody", {
            "record_kind": authority.REVOCATION_KIND, "grant_id": payload["grant_id"],
            "revoked_by": "nobody", "revoked_at": self.console.stamp(),
            "standing": "RECORDED"})
        self.assertIn(payload["grant_id"],
                      authority.live_grants(self.record.reconstruct()))
        # And it still admits nothing, which is the other half of the same rule.
        with self.assertRaises(AuthorityRefused):
            self.console.open_channel("ana", "governance channel", "governance")


if __name__ == "__main__":
    unittest.main()
