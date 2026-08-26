"""The BACK/permits-office operations: minting, withdrawing and listing grants.

`authority.py` owns what a grant is and whether one admits an operation.
This module owns the three operations `contracts/capability-offices.json` puts at
`BACK/permits-office` - `console.grant`, `console.revoke` and `console.list-grants` -
because they are transitions over the journal rather than facts about a record, and
because the bootstrap below is a rule about issuing, not about checking.

Bootstrap. A node whose every grant needs a prior grant can never issue its
first one. The Asset Service closed the same hole with a recorded root issuer,
and this module closes it the same way: against a journal where no node has yet
opened this node's permits office, the first issuer becomes this node's root and
self-issues `grant:authority` and `revoke:authority`. Those are ordinary grant
records - visible to `console.list-grants`, revocable, and attributable by
`granted_by` - not a code path that skips the check. The condition is once-ever
rather than once-while-live: a revocation does not remove the grant record it
counters, so no second bootstrap can be provoked by revoking the first one.
Revoking the root's `grant:authority` therefore ends grant issue on that node,
which is what append-preserving revocation means and not a defect.

Every grant record carries `node_id`, the node whose office minted it, and
`check` matches on it. Without that field the office was decorative: a grant is
matched on operator, capability and scope, none of which mention a node, so a
console opened under any other node identifier could mint a grant that a
`node:local` check would then honour. That was reachable from the shipped CLI
with one `--node` flag, and it defeated the six operations that were already
enforcing as well as the nine guarded on 2026-08-25.

What that field does and does not establish, stated plainly because the
difference matters:

*It establishes the partition.* `check` compares node identifiers with `==` on
`str` and transforms them in no other way - no case folding, no normalisation,
no prefix or glob interpretation - so the namespaces the check induces are
exactly string identity. Two spellings that differ by any byte are two nodes;
no spelling reaches another node's grants. `services/console/tests/
test_enforced_authority.py` drives that as a property over a corpus of spellings
rather than as a list of the escapes somebody thought of.

*It does not establish the identity.* `node_id` is whatever the process that
opened the `ConsoleService` passed to the constructor, and there is no Identity
service, node key or registry lookup behind it. `contracts/node-identity.schema.json`
constrains the shape and nothing attests the claim. So a grant record proves
which namespace it was minted into and does not prove that namespace was
entitled to the name. What keeps that from being a bypass is the bootstrap, not
the field: opening a node's office is once-ever and recorded, so a caller
asserting a name whose office is already open lands against a `grant:authority`
it does not hold. On a store where a node's office has never been opened, the
first issuer takes it - the declared first-issuer default, unchanged, and the
same one the Asset Service records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from soveraeign_console_service import append
from soveraeign_console_service.authority import (
    GRANT_CAPABILITY,
    GRANT_KIND,
    READ_AUTHORITY_CAPABILITY,
    REVOCATION_KIND,
    REVOKE_CAPABILITY,
    grant_payload,
    grant_record,
    held,
    require,
    revocation_payload,
    root_issuer,
)
from soveraeign_console_service.refusals import (
    LastIssuerStanding,
    UnknownRecord,
)

if TYPE_CHECKING:  # pragma: no cover - broken at runtime; core imports this module
    from soveraeign_console_service.core import ConsoleService


def _genesis(console: "ConsoleService", issuer: str) -> None:
    """Record this node's root issuer as two ordinary, revocable grants.

    Called only against a journal that has never carried a grant. Nothing here
    skips the check that follows it: the check reads these records like any other.
    """
    for capability in (GRANT_CAPABILITY, REVOKE_CAPABILITY):
        payload = grant_payload(issuer, capability, console.node_id, issuer,
                                console.stamp(), console.node_id)
        append.emit(console.record, GRANT_KIND, payload["grant_id"], issuer, payload,
                    "console.grant")


def issue(console: "ConsoleService", operator_id: str, capability: str, scope: str,
          granted_by: str) -> dict[str, Any]:
    """`console.grant`: record a live grant, if the issuer holds one to issue it.

    Before 2026-08-25 this checked nothing, so any caller could write itself any
    grant and the permits office was decorative.
    """
    entries = console.record.reconstruct()
    if root_issuer(entries, console.node_id) is None:
        _genesis(console, granted_by)
        entries = console.record.reconstruct()
    payload = grant_payload(operator_id, capability, scope, granted_by, console.stamp(),
                            console.node_id)
    admitting = require(console.record, entries, console.node_id, granted_by,
                        GRANT_CAPABILITY, console.node_id, "console.grant",
                        payload["grant_id"])
    return append.emit(console.record, GRANT_KIND, payload["grant_id"], granted_by,
                       payload, "console.grant", [admitting])


def withdraw(console: "ConsoleService", grant_id: str,
             revoked_by: str) -> dict[str, Any]:
    """`console.revoke`: withdraw a grant, if the revoker holds one to withdraw it.

    A node revokes its own grants and no one else's. Without that a console opened
    under any other identifier could take its own office by bootstrap and then
    counter this node's root grant, which ends grant issue here for good - the
    denial of service that mirrors the minting bypass.

    The node's last live `grant:authority` at node scope cannot be withdrawn, and
    neither can its last `revoke:authority` - withdrawing that one ends revocation
    on the node, so a compromised grant could never be countered afterwards. Two
    other shapes were available and both cost more. Making the root grant permanently
    irrevocable would mean a root can never be demoted, which is the whole point of
    having revocation. Reopening the bootstrap when no live issuer remains would turn
    an availability bug into a takeover window: the office would stand open and the
    next caller of any name would take it, which is exactly the once-ever rule that
    closed the minting bypass. Refusing only the *last* one keeps both - grant a
    successor, then withdraw the predecessor - and never leaves the office unowned.

    The grant spent here is never the grant withdrawn here. It is checked twice on
    purpose, over one replay: first that the revoker holds `revoke:authority` at all,
    which is the authority question and has to precede every precondition so an
    ungranted caller learns nothing about the office; then, after the last-issuer
    rule has had its say, that some grant *other than the target* admits the
    withdrawal. Only the second can cite, and a revoker spending the grant it is
    withdrawing left a `COMMITTED` receipt naming a grant the same record revoked.
    """
    entries = console.record.reconstruct()
    target = grant_record(entries, grant_id)
    if target is None:
        # `grant_exists` is a declared precondition and this branch enforced nothing,
        # so `revoke --grant ""` appended a revocation naming no grant and exited 0.
        raise UnknownRecord(grant_id)
    if target.get("node_id") != console.node_id:
        # Answered as missing, not as another node's: this runs before the authority
        # check, so a caller holding nothing could otherwise sweep grant ids and learn
        # which existed and which office issued them.
        raise UnknownRecord(grant_id)
    require(console.record, entries, console.node_id, revoked_by,
            REVOKE_CAPABILITY, console.node_id, "console.revoke", grant_id)
    capability = target["capability"]
    if (capability in OFFICE_CAPABILITIES and target["scope"] == console.node_id
            and not _other_holders(entries, console.node_id, capability, grant_id)):
        raise append.refuse(
            console.record,
            LastIssuerStanding(
                f"grant {grant_id} is this node's only live {capability} at node "
                f"scope; record another before withdrawing it"),
            "console.revoke", grant_id, revoked_by)
    admitting = require(console.record, entries, console.node_id, revoked_by,
                        REVOKE_CAPABILITY, console.node_id, "console.revoke", grant_id,
                        excluding=grant_id)
    payload = revocation_payload(grant_id, revoked_by, console.stamp(),
                                 console.node_id)
    return append.emit(console.record, REVOCATION_KIND, grant_id, revoked_by,
                       payload, "console.revoke", [admitting])


#: The two capabilities the permits office runs on. Each is checked at node scope by
#: the transition that spends it - `issue` requires `grant:authority` scoped to the
#: node, `withdraw` requires `revoke:authority` scoped to the node - so each is the
#: office's single point of failure and each needs the same last-holder rule.
OFFICE_CAPABILITIES = (GRANT_CAPABILITY, REVOKE_CAPABILITY)


def _other_holders(entries: list[dict[str, Any]], node_id: str, capability: str,
                   besides: str) -> list[dict[str, Any]]:
    """Live grants of one office capability that can actually still spend it.

    Scope is part of the predicate and was missing until 2026-08-25. `issue` requires
    a `grant:authority` whose scope *equals* the node, so a `grant:authority` recorded
    at any other scope admits nothing - and a guard that counted it as an issuer let
    the last real one be withdrawn. Four ordinary CLI commands then left the office
    unowned and unrecoverable, which is the state this rule exists to prevent: a
    mistyped `--scope` and a routine root rotation, no attacker involved.

    The declared precondition is named `another_issuer_remains`. An issuer is a grant
    that can issue, not a record that carries the name.
    """
    return [record for record in held(entries, None, node_id)
            if record["capability"] == capability
            and record["scope"] == node_id
            and record["grant_id"] != besides]


def listing(console: "ConsoleService", reader_id: str,
            operator_id: str | None = None) -> list[dict[str, Any]]:
    """`console.list-grants`: who holds what on this node, for a reader admitted to look.

    Who may do what is node state, not the reader's own record, so the read is
    scoped to the node even when the reader asks only about itself.
    """
    entries = console.record.reconstruct()
    require(console.record, entries, console.node_id, reader_id,
            READ_AUTHORITY_CAPABILITY, console.node_id, "console.list-grants",
            console.node_id)
    return held(entries, operator_id, console.node_id)
