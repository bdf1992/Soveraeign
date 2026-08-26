"""Typed, scoped, live grants recorded in the journal rather than held in a process.

`AGENTS.md`: every consequential transition uses a typed, scoped, live grant at
the operation boundary, and no participant receives authority merely by operating
successfully. A grant kept in a process variable satisfies none of that - it
disappears at exit, it is not attributable, and it cannot be inspected after the
fact. So a grant is a journal record like anything else.

Revocation appends rather than deletes. A revoked grant stops admitting the next
operation; it never reaches back and unmakes an operation already committed under
it, and the grant record stays readable so the history of who could do what
remains reconstructable.

Identity is still a string. There is no Identity service yet, so this module
records who granted what without being able to check that the granter is who it
says it is. That gap is named in `services/console/KNOWN-GAPS.md`; it is a
missing service, not an oversight in this module. What this module can check, and
now does, is that the granter holds a live grant to grant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import uuid

from soveraeign_console_service import append
from soveraeign_console_service.refusals import AuthorityRefused
from soveraeign_record_service import RecordService

if TYPE_CHECKING:  # pragma: no cover - broken at runtime; core imports this module
    from soveraeign_console_service.core import ConsoleService

GRANT_KIND = "authority-grant"
REVOCATION_KIND = "authority-revocation"


POST_CAPABILITY = "post:message"
PUBLISH_CAPABILITY = "publish:thread"
GRANT_CAPABILITY = "grant:authority"
REVOKE_CAPABILITY = "revoke:authority"
READ_AUTHORITY_CAPABILITY = "read:authority"
# The capability string this service actually passes to the authority check, per
# operation. Named here rather than left at the call sites so a reader - and
# `discovery.operations` - can see what a grant has to say to admit an operation.
# These agree with `contracts/capability-offices.json`, and
# `services/console/tests/test_discovery.py` fails if any of them stops agreeing.
ENFORCED_AUTHORITY: dict[str, str] = {
    "console.open-channel": "open:channel",
    "console.open-thread": "open:thread",
    # `archive-thread` archives THE thread: the lifecycle record lands in the shared
    # journal and no operator may post into it afterwards. Bdo, 2026-08-24: archiving a
    # thread for yourself would not need its own grant, archiving the thread does. So
    # this enforces `archive:thread` and no longer rides on `open:thread`, which
    # narrows the ability on purpose. A per-operator hide is a different operation and
    # does not exist. decisions/0054.
    "console.archive-thread": "archive:thread",
    "console.publish-thread": PUBLISH_CAPABILITY,
    "console.withdraw-publication": PUBLISH_CAPABILITY,
    "console.post": POST_CAPABILITY,
    # The nine below were built, callable and checking nothing: any caller was
    # admitted, `console.grant` and `console.revoke` among them, so anyone reaching
    # the service could write itself a grant. Bdo ruled 2026-08-25 to guard all nine,
    # having been told that a check removes an ability from whoever can call them
    # today - the same call he made for `archive:thread` in decisions/0054.
    "console.grant": GRANT_CAPABILITY,
    "console.revoke": REVOKE_CAPABILITY,
    "console.list-grants": READ_AUTHORITY_CAPABILITY,
    "console.open-session": "open:session",
    "console.close-session": "close:session",
    "console.discover-operations": "read:session",
    "console.session-context": "read:session",
    "console.read-thread": "read:thread",
    "console.list-publications": "read:thread",
}

#: What each enforced capability's scope names. A capability name says what may be
#: done; the scope says over what, and a grant admits only an exact match. Recorded
#: here for the same reason `ENFORCED_AUTHORITY` is: a scope chosen at a call site
#: and written down nowhere cannot be audited, and an operator cannot be told which
#: grant to ask for. `NODE` is the whole node this console serves.
ENFORCED_SCOPE: dict[str, str] = {
    "console.open-channel": "DOMAIN",
    "console.open-thread": "CHANNEL",
    "console.archive-thread": "CHANNEL",
    "console.publish-thread": "THREAD",
    "console.withdraw-publication": "THREAD",
    "console.post": "THREAD",
    # The permits office governs the node's grants as a whole, so its three
    # capabilities scope to the node. Scoping `grant:authority` to the capability
    # being issued would read tighter and cannot bootstrap: the root's first grant
    # would have to name every capability the node will ever declare.
    "console.grant": "NODE",
    "console.revoke": "NODE",
    "console.list-grants": "NODE",
    # A session belongs to an operator, so both session lifecycle grants scope to the
    # operator rather than to one session id. Scoping the close to the session would
    # make a grant per session, expiring the moment it was useful.
    "console.open-session": "OPERATOR",
    "console.close-session": "OPERATOR",
    "console.discover-operations": "OPERATOR",
    "console.session-context": "OPERATOR",
    "console.read-thread": "THREAD",
    # The publication list is every thread this node renders outwardly, not one
    # thread, so it is a node-wide read and scopes to the node.
    "console.list-publications": "NODE",
}


def grant_payload(operator_id: str, capability: str, scope: str, granted_by: str,
                  granted_at: str, node_id: str) -> dict[str, Any]:
    """The record admitting one operator to one capability over one scope on one node.

    `node_id` is written from the minting service's own identity. It is never taken
    from an argument the caller of `console.grant` supplies, so a grant cannot name a
    node other than the one whose office issued it.
    """
    return {"grant_id": f"grant_{uuid.uuid4().hex[:16]}", "node_id": node_id,
            "operator_id": operator_id, "capability": capability, "scope": scope,
            "granted_by": granted_by, "granted_at": granted_at, "standing": "RECORDED"}


def revocation_payload(grant_id: str, revoked_by: str, revoked_at: str,
                       node_id: str) -> dict[str, Any]:
    """The record withdrawing one grant. The grant record itself is left alone.

    It names the node whose permits office withdrew it, as the grant does, so a
    journal carrying more than one console does not read as one office.
    """
    return {"grant_id": grant_id, "node_id": node_id, "revoked_by": revoked_by,
            "revoked_at": revoked_at, "standing": "RECORDED"}


def live_grants(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Fold a replayed journal into the grants that are live right now.

    A revocation counts only against a grant its own office issued. `permits.withdraw`
    refuses to withdraw another node's grant, and `revocation_payload` records the node
    that withdrew "so a journal carrying more than one console does not read as one
    office" - but this fold matched on `grant_id` alone, so a revocation appended under
    `node:peer` still killed a `node:local` grant and undid both. Reachable only through
    a crossing, which has no transport in Phase I; the field was already on the record.
    """
    granted: dict[str, dict[str, Any]] = {}
    revoked: list[dict[str, Any]] = []
    for entry in entries:
        payload = entry["payload"]
        kind = payload.get("record_kind")
        if kind == GRANT_KIND:
            granted[payload["grant_id"]] = payload
        elif kind == REVOCATION_KIND:
            revoked.append(payload)
    withdrawn = {payload["grant_id"] for payload in revoked
                 if payload["grant_id"] in granted
                 and payload.get("node_id") == granted[payload["grant_id"]].get("node_id")}
    return {grant_id: record for grant_id, record in granted.items()
            if grant_id not in withdrawn}


def held(entries: list[dict[str, Any]], operator_id: str | None = None,
         node_id: str | None = None) -> list[dict[str, Any]]:
    """Every grant live right now, optionally narrowed to one operator and one node.

    A reader that did not narrow by node would report a grant minted elsewhere as
    one this node honours, which is the thing `check` refuses.
    """
    return sorted((record for record in live_grants(entries).values()
                   if (operator_id is None or record["operator_id"] == operator_id)
                   and (node_id is None or record.get("node_id") == node_id)),
                  key=lambda record: record["grant_id"])


def grant_record(entries: list[dict[str, Any]], grant_id: str) -> dict[str, Any] | None:
    """One grant record by id, revoked or not, or None if this journal has no such grant.

    Revoked grants are included on purpose: a revocation has to be able to name the
    node its target belonged to, and a revoked grant is still a record.
    """
    for entry in entries:
        payload = entry["payload"]
        if payload.get("record_kind") == GRANT_KIND and payload["grant_id"] == grant_id:
            return payload
    return None


def root_issuer(entries: list[dict[str, Any]], node_id: str) -> str | None:
    """Who first took `grant:authority` over this node, if anyone has.

    The origin of one node's authority, read back out of the record rather than
    configured. `None` means this node's permits office has never been opened, which
    is the one condition under which `issue` bootstraps.

    Per node, not per journal. One journal can carry more than one console - a peer's
    records reach a local journal through a crossing, and the tests drive two node
    identities over one store - and a journal-wide condition would let whichever
    console opened first take a root, leaving every other node on that journal
    permanently unable to issue its first grant.

    Read off the grant's own `node_id`, which the minting service wrote, rather than
    off its scope, which is an argument the caller chose. A caller that could pick the
    field this loop matches on could hide an open office and provoke a second
    bootstrap.
    """
    for entry in entries:
        payload = entry["payload"]
        if (payload.get("record_kind") == GRANT_KIND
                and payload["capability"] == GRANT_CAPABILITY
                and payload.get("node_id") == node_id):
            return payload["granted_by"]
    return None


def require(record: RecordService, entries: list[dict[str, Any]], node_id: str,
            operator_id: str, capability: str, scope: str, event: str,
            subject: str, excluding: str = "") -> str:
    """The live grant admitting this transition, or a refusal that is written down.

    `check` reads and cannot append, so the refusal it raises used to leave no trace -
    the one refusal in this service that did not, against `append.py`'s rule that a
    refusal leaving nothing cannot be told from an attempt nobody made. The caller
    names the event and subject because only it knows which transition was tried.

    The Asset Service's `Authority.require` does the same thing at the same boundary;
    a participant whose authority check refused silently would diverge from it.
    """
    try:
        return check(entries, node_id, operator_id, capability, scope, excluding)
    except AuthorityRefused as refused:
        raise append.refuse(record, refused, event, subject, operator_id) from None


def check(entries: list[dict[str, Any]], node_id: str, operator_id: str,
          capability: str, scope: str, excluding: str = "") -> str:
    """Return the id of a live grant admitting this operation on this node, or refuse.

    Which of several live matches is returned is a decision, not an accident of how
    the fold happens to be ordered: the id goes on the receipt as the authority a
    committed operation was admitted under, so it is a record-integrity claim. Two
    rules settle it, and `services/console/tests/test_enforced_authority.py` fails if
    either is dropped.

    *The newest live match admits.* `live_grants` folds the journal in append order,
    so the last match is the most recently issued grant still standing. Newest rather
    than oldest because an issuer's latest decision about a capability is the one that
    describes the node now; citing the earliest would attribute a commit to a decision
    a later issuance has already spoken over. Newest means latest in the journal, not
    latest timestamp: two grants recorded in the same second are still ordered by the
    record that carries them. Reversing this rule to `matches[0]` used to pass every
    check in the repository.

    *A grant cannot admit the record that withdraws it.* `excluding` names a grant
    that may not admit this operation, and `console.revoke` passes its target. Without
    it a revoker whose only live `revoke:authority` was the grant being withdrawn
    spent that grant on its own withdrawal, and the terminal `COMMITTED` receipt then
    cited, as the authority admitting the operation, a grant the same operation had
    just revoked - readable straight out of the journal, and false about the state at
    the position the receipt lands. Revocation still never reaches back and unmakes an
    operation committed before it; this is about the one operation that revokes and
    commits at once.

    That second rule closes the case one writer can reach on its own, and no more.
    Every console operation reads the journal, decides, and appends in three separate
    `RecordService` transactions, so a *second* writer on the same store can append a
    revocation of the admitting grant in between, and the receipt then lands after it.
    Reproduced on 2026-08-26 with two ordinary processes against one `--root`. Nothing
    in this service closes it: it needs a read-and-append the Record Service performs
    under one transaction, or a compare-and-append against the head the check read, and
    `RecordService.append` offers neither. Recorded in `services/console/KNOWN-GAPS.md`
    rather than narrowed here, because a window made smaller reads as a window closed.

    The refusal names the capability and not the scope: a scope is an operator id, a
    channel or a thread, and telling a caller that holds nothing which one it just
    missed discloses who owns the record. It stays on the exception for a caller that
    already knows it.

    Four exact comparisons on `str`, and no other reading of any of them. The node is
    one of the four because a journal can carry grants minted by more than one node
    and the other three say nothing about which. Nothing here folds case, strips
    whitespace, resolves a prefix or expands a pattern, so the set of node identifiers
    that reach a given node's grants is the one identifier equal to it. A grant whose
    record predates this field carries no node and matches nothing, which stops an
    older store's grants being honoured under a name they never named.
    """
    matches = [record for record in live_grants(entries).values()
               if record.get("node_id") == node_id
               and record["operator_id"] == operator_id
               and record["capability"] == capability
               and record["scope"] == scope
               and record["grant_id"] != excluding]
    if not matches:
        withheld = (" other than the one being withdrawn" if excluding else "")
        raise AuthorityRefused(
            f"{operator_id} holds no live {capability} grant{withheld} for this operation",
            capability=capability, scope=scope)
    return matches[-1]["grant_id"]
