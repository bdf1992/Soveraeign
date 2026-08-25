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


def thread(entries: list[dict[str, Any]], thread_id: str) -> dict[str, Any]:
    """One thread's current state, including any archival that landed after it opened."""
    return latest(entries, THREAD_KINDS, "thread_id", thread_id)


def session(entries: list[dict[str, Any]], session_id: str) -> dict[str, Any]:
    """One operator session's current state, including its close."""
    return latest(entries, SESSION_KINDS, "session_id", session_id)


def publication(entries: list[dict[str, Any]], publication_id: str) -> dict[str, Any]:
    """One publication mark's current state, including any withdrawal."""
    return latest(entries, PUBLICATION_KINDS, "publication_id", publication_id)
