"""The publication lifecycle: what marks a thread readable outside, and what ends it.

`core.py` owns the threaded record path an operator drives inside the node.
Publishing points the other way, so the two transitions that move a publication live
here with the record shapes they append, the way `sessions.py` owns the operator
session and `permits.py` owns the permits office. This is the only console concern
whose effect is visible to people who are not members of anything.

Both transitions refuse a thread another node owns. Publishing a peer's thread would
republish its record under this node's name; withdrawing a peer's publication would
take down a mark this node never made.

`contracts/publication.schema.json` owns the shape; `contracts/public-projection.schema.json`
renders it. A projection never decides what is public - it reads what was recorded here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from soveraeign_console_service import append, reads
from soveraeign_console_service.authority import PUBLISH_CAPABILITY

if TYPE_CHECKING:  # pragma: no cover - broken at runtime; core imports this module
    from soveraeign_console_service.core import ConsoleService

PUBLISH_EVENT = "console.publish-thread"
WITHDRAW_EVENT = "console.withdraw-publication"
VISIBILITY = "PUBLIC"
PUBLISHED = "PUBLISHED"
WITHDRAWN = "WITHDRAWN"


def publication_payload(node_id: str, publication_id: str, thread_id: str,
                        published_by: str, published_at: str,
                        standing: str) -> dict[str, Any]:
    """The record marking one thread readable outside the node."""
    return {"node_id": node_id, "publication_id": publication_id, "thread_id": thread_id,
            "visibility": VISIBILITY, "lifecycle": PUBLISHED, "published_by": published_by,
            "published_at": published_at, "withdrawn_at": None, "standing": standing}


def withdrawal_payload(node_id: str, publication_id: str, thread_id: str,
                       withdrawn_at: str, standing: str) -> dict[str, Any]:
    """The record ending one publication.

    It carries no `published_by` and no `published_at`. Those belong to the mark this
    entry folds onto, and restating them here would let a withdrawal quietly rewrite
    who published a thread and when.
    """
    return {"node_id": node_id, "publication_id": publication_id, "thread_id": thread_id,
            "lifecycle": WITHDRAWN, "withdrawn_at": withdrawn_at, "standing": standing}


def publish_thread(console: "ConsoleService", operator_id: str, thread_id: str,
                   publication_id: str, standing: str) -> dict[str, Any]:
    """`console.publish-thread`: mark a thread readable outside the node.

    This is the record `contracts/public-projection.schema.json` renders. The
    projection decides nothing; it reads what this transition wrote, which is why
    publishing needs its own capability rather than riding on `open-thread`.
    """
    entries = console.record.reconstruct()
    # Authority first: the scope is the thread id the caller supplied.
    grant = console.authorize(operator_id, PUBLISH_CAPABILITY, thread_id, PUBLISH_EVENT,
                              publication_id, entries)
    console.owned(console.by_id(reads.thread, thread_id, entries, PUBLISH_EVENT,
                                operator_id),
                  thread_id, PUBLISH_EVENT, operator_id)
    return append.emit(
        console.record, "publication", publication_id, operator_id,
        publication_payload(console.node_id, publication_id, thread_id, operator_id,
                            console.stamp(), standing),
        PUBLISH_EVENT, [grant])


def withdraw_publication(console: "ConsoleService", operator_id: str,
                         publication_id: str, standing: str) -> dict[str, Any]:
    """`console.withdraw-publication`: stop rendering a thread outwardly.

    Withdrawal appends. It never claims the thread was not public, and it never
    claims nobody read it while it was.
    """
    entries = console.record.reconstruct()
    # The grant's scope is the thread this mark names, which cannot be known without
    # reading the mark, so an unearned caller gets the missing-record answer.
    mark = console.held_record(
        console.by_id(reads.publication, publication_id, entries, WITHDRAW_EVENT,
                      operator_id),
        publication_id, WITHDRAW_EVENT, operator_id)
    grant = console.authorize(operator_id, PUBLISH_CAPABILITY, mark["thread_id"],
                              WITHDRAW_EVENT, publication_id, entries)
    return append.emit(
        console.record, "publication-lifecycle", publication_id, operator_id,
        withdrawal_payload(console.node_id, publication_id, mark["thread_id"],
                           console.stamp(), standing),
        WITHDRAW_EVENT, [grant])
