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
records who granted what without being able to check that the granter held the
authority to grant it. That gap is named in `services/console/KNOWN-GAPS.md`; it
is a missing service, not an oversight in this module.
"""

from __future__ import annotations

from typing import Any
import uuid

from soveraeign_console_service import append
from soveraeign_console_service.refusals import AuthorityRefused
from soveraeign_record_service import RecordService

GRANT_KIND = "authority-grant"
REVOCATION_KIND = "authority-revocation"


POST_CAPABILITY = "post:message"
PUBLISH_CAPABILITY = "publish:thread"
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
}


def grant_payload(operator_id: str, capability: str, scope: str, granted_by: str,
                  granted_at: str) -> dict[str, Any]:
    """The record admitting one operator to one capability over one scope."""
    return {"grant_id": f"grant_{uuid.uuid4().hex[:16]}", "operator_id": operator_id,
            "capability": capability, "scope": scope, "granted_by": granted_by,
            "granted_at": granted_at, "standing": "RECORDED"}


def revocation_payload(grant_id: str, revoked_by: str, revoked_at: str) -> dict[str, Any]:
    """The record withdrawing one grant. The grant record itself is left alone."""
    return {"grant_id": grant_id, "revoked_by": revoked_by, "revoked_at": revoked_at,
            "standing": "RECORDED"}


def live_grants(entries: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Fold a replayed journal into the grants that are live right now."""
    granted: dict[str, dict[str, Any]] = {}
    revoked: set[str] = set()
    for entry in entries:
        payload = entry["payload"]
        kind = payload.get("record_kind")
        if kind == GRANT_KIND:
            granted[payload["grant_id"]] = payload
        elif kind == REVOCATION_KIND:
            revoked.add(payload["grant_id"])
    return {grant_id: record for grant_id, record in granted.items() if grant_id not in revoked}


def require(record: RecordService, entries: list[dict[str, Any]], operator_id: str,
            capability: str, scope: str, event: str, subject: str) -> str:
    """The live grant admitting this transition, or a refusal that is written down.

    `check` reads and cannot append, so the refusal it raises used to leave no trace -
    the one refusal in this service that did not, against `append.py`'s rule that a
    refusal leaving nothing cannot be told from an attempt nobody made. The caller
    names the event and subject because only it knows which transition was tried.

    The Asset Service's `Authority.require` does the same thing at the same boundary;
    a participant whose authority check refused silently would diverge from it.
    """
    try:
        return check(entries, operator_id, capability, scope)
    except AuthorityRefused as refused:
        raise append.refuse(record, refused, event, subject, operator_id) from None


def check(entries: list[dict[str, Any]], operator_id: str, capability: str,
          scope: str) -> str:
    """Return the id of a live grant admitting this operation, or refuse.

    The newest matching grant wins, so re-granting after a revocation restores the
    capability without rewriting the revocation that came before it. Newest means
    latest in the journal, not latest timestamp: two grants recorded in the same
    second are still ordered by the record that carries them.
    """
    matches = [record for record in live_grants(entries).values()
               if record["operator_id"] == operator_id
               and record["capability"] == capability
               and record["scope"] == scope]
    if not matches:
        raise AuthorityRefused(
            f"{operator_id} holds no live {capability} grant scoped to {scope}")
    return matches[-1]["grant_id"]
