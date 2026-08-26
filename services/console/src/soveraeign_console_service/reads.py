"""Reading one console record back out of the journal.

A transition needs to know the current state of the thing it is about to change: is
this thread archived, is this session closed, which thread does this publication mark.
That is a different job from performing the transition, and it has one rule of its own
worth stating in a module rather than repeating at each call site.

The rule is folding. A console record is written once and then amended by lifecycle
entries that name it, so its current state is every entry naming it, applied in append
order. Reading only the first entry would miss the archive; reading only the last would
lose the fields the amendment does not restate.

Nothing here verifies the journal. Callers pass entries from `RecordService.reconstruct`,
which checks the digest chain first; folding an unverified read would produce a
plausible state out of a rewritten history.
"""

from __future__ import annotations

from typing import Any

from soveraeign_console_service.refusals import UnknownRecord

CHANNEL_KINDS = ("channel",)
THREAD_KINDS = ("thread", "thread-lifecycle")
SESSION_KINDS = ("operator-session", "operator-session-lifecycle")
PUBLICATION_KINDS = ("publication", "publication-lifecycle")


def latest(entries: list[dict[str, Any]], kinds: tuple[str, ...], key: str,
           value: str) -> dict[str, Any]:
    """Fold every journal entry naming this record, in append order."""
    found: dict[str, Any] = {}
    for entry in entries:
        payload = entry["payload"]
        if payload.get("record_kind") in kinds and payload.get(key) == value:
            found.update(payload)
    if not found:
        raise UnknownRecord(value)
    return found


def foreign(record: dict[str, Any], node_id: str) -> str | None:
    """The reason this record belongs to another node, or None when it is ours.

    Returned rather than raised so a caller names the operation it was refusing:
    the same fact refuses an archive, a publish, a read and a post, and each says
    what it would have done. A record written before console records carried a node
    reads as foreign to every node, which is the safe direction.

    The reason names this node and never the owning one. Saying which peer holds a
    record tells a caller something about a node it has no standing on, and the
    caller already knows which node it asked.

    This is the check that makes node-bound authority mean anything. Binding a grant
    to the node that minted it stops a grant crossing; it does not stop the node that
    minted it reading and writing another node's records with a grant of its own,
    because a node identifier is unbounded and anyone refused one office can open
    another. An independent witness walked exactly that on 2026-08-25.
    """
    if record.get("node_id") == node_id:
        return None
    return f"is not a record of {node_id}"


def local(entries: list[dict[str, Any]], node_id: str) -> list[dict[str, Any]]:
    """Only the entries this node made, for folds that have no single subject.

    A listing cannot refuse about one record, so it filters instead: another node's
    channels, threads, posts, sessions and publications are not in the answer at all.
    Entries the console did not write - a receipt, a peer's record - carry no
    `record_kind` this service folds, so they are filtered by the same rule.
    """
    return [entry for entry in entries
            if entry["payload"].get("node_id") == node_id]


def channel(entries: list[dict[str, Any]], channel_id: str) -> dict[str, Any]:
    """One channel's current state. Threads open into it, so it has to exist."""
    return latest(entries, CHANNEL_KINDS, "channel_id", channel_id)


def thread(entries: list[dict[str, Any]], thread_id: str) -> dict[str, Any]:
    """One thread's current state, including any archival that landed after it opened."""
    return latest(entries, THREAD_KINDS, "thread_id", thread_id)


def session(entries: list[dict[str, Any]], session_id: str) -> dict[str, Any]:
    """One operator session's current state, including its close."""
    return latest(entries, SESSION_KINDS, "session_id", session_id)


def publication(entries: list[dict[str, Any]], publication_id: str) -> dict[str, Any]:
    """One publication mark's current state, including any withdrawal."""
    return latest(entries, PUBLICATION_KINDS, "publication_id", publication_id)
