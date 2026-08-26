"""One attributed turn in a thread: the console transition that has an effect.

`core.py` owns channels and threads. This owns the post, and it is a module of its
own because it is the one console operation that puts new bytes on disk and the one
whose record another operator later reads back as somebody's word. Everything it
refuses is a way that record could have been wrong about who spoke, where, or on
whose authority, and every refusal is written down, so an attempt nobody was
admitted to is not the same as an attempt nobody made.

Three of those refusals answer the same question from different sides: a session
identifies an operator but holding one does not make you that operator
(`ACTOR_ATTRIBUTION_MISMATCH`); a closed session is a read position, not a writer
(`SESSION_CLOSED`); and a thread on another node is not this node's to write into
(`FOREIGN_NODE_RECORD`, through `ConsoleService.owned`). The first of those was
missing until 2026-08-25: this read the operator off the session and checked that
operator's grants, so a caller who knew any session id wrote a post signed with its
owner's name, and the record it left was indistinguishable from one the owner wrote.

Parity is structural rather than promised, which is what
`conformance/006-thread-post-parity.yaml` requires: a HUMAN post and a MODEL post
take this one function and check one capability, and the binding an operator reached
through appears only as `interface_id` on the receipt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable
import hashlib

from soveraeign_console_service import append
from soveraeign_console_service.authority import POST_CAPABILITY
from soveraeign_console_service.refusals import (
    ActorAttributionMismatch,
    ModelClaimWithoutProposal,
    SessionClosed,
    ThreadArchived,
)

if TYPE_CHECKING:  # pragma: no cover - broken at runtime; core imports this module
    from soveraeign_console_service.core import ConsoleService

POST_OPERATION = "console.post"


def post(console: "ConsoleService", operator_id: str, session_id: str, thread_id: str,
         body: bytes, post_id: str, standing: str, mentions: Iterable[str],
         claims: bool, proposal_id: str | None) -> dict[str, Any]:
    """`console.post`: record one attributed turn, or refuse and say so.

    `operator_id` is who is posting and must be the session's own operator.

    No defaults here. `ConsoleService.post` is the only caller and always supplies
    every argument, so a default on this side would be a value nothing can reach and
    nothing can test - which is how a wrong one survives.
    """
    # One verified replay serves all three reads below. Replaying per lookup made a
    # post cost O(journal) three times over and the verification budget noticed
    # before any user would have.
    entries = console.record.reconstruct()
    refuse = console.refusal
    # Authority first. Its scope is the thread id the caller supplied, so checking it
    # reads nothing, and an ungranted caller cannot sweep session ids for existence.
    grant = console.authorize(operator_id, POST_CAPABILITY, thread_id, POST_OPERATION,
                              post_id, entries)
    # The grant is over the thread, not over this session, so a session belonging to
    # another node is still answered as simply unknown.
    session = console.held_session(session_id, entries)
    if session["operator_id"] != operator_id:
        owner = session["operator_id"]
        raise refuse(ActorAttributionMismatch(f"session {session_id} belongs to {owner}"),
                     POST_OPERATION, post_id, operator_id)
    if session["lifecycle"] != "OPEN":
        raise refuse(SessionClosed(f"session {session_id} is CLOSED"),
                     POST_OPERATION, post_id, operator_id)
    if console.thread(thread_id, entries, POST_OPERATION,
                      operator_id)["lifecycle"] != "OPEN":
        raise refuse(ThreadArchived(f"thread {thread_id} is ARCHIVED"),
                     POST_OPERATION, post_id, operator_id)
    if session["actor_kind"] == "MODEL" and claims and proposal_id is None:
        raise refuse(
            ModelClaimWithoutProposal(
                "a MODEL post that claims enters the kernel as a Proposal first"),
            POST_OPERATION, post_id, operator_id)
    digest = hashlib.sha256(body).hexdigest()
    (console.posts / digest).write_bytes(body)
    return append.emit(console.record, "post", post_id, operator_id, {
        "node_id": console.node_id,
        "post_id": post_id, "thread_id": thread_id, "actor_id": operator_id,
        "actor_kind": session["actor_kind"], "content_address": f"posts/{digest}",
        "content_digest": f"sha256:{digest}", "mentions": sorted(set(mentions)),
        "proposal_id": proposal_id, "posted_at": console.stamp(),
        "session_id": session_id, "binding_id": session["binding_id"],
        "standing": standing,
    }, POST_OPERATION, [grant])
