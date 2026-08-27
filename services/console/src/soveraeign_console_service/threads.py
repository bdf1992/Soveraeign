"""The channel and thread lifecycle: where a conversation is opened and where it ends.

`core.py` owns the service object, the append path and the record reads every
transition depends on. This module owns the three transitions that move a channel or
a thread, next to each other, the way `sessions.py` owns the operator session,
`posts.py` owns the post and `permits.py` owns the permits office.

The three differ in one thing worth reading together rather than apart: when the
authority check happens relative to the read.

`open_channel` and `open_thread` check first. Their grant's scope is a domain or a
channel id the caller supplied, so nothing has to be read to check it, and an
ungranted caller learns nothing about which channels exist.

`archive_thread` reads first. Its grant's scope is the thread's channel, which cannot
be known without reading the thread, so an unearned caller gets the missing-record
answer - the same one an absent thread gets, which is what `core.held_record` is for.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from soveraeign_console_service import append
from soveraeign_console_service.authority import ENFORCED_AUTHORITY
from soveraeign_console_service.refusals import PinIncomplete

if TYPE_CHECKING:  # pragma: no cover - broken at runtime; core imports this module
    from soveraeign_console_service.core import ConsoleService

OPEN_CHANNEL_EVENT = "console.open-channel"
OPEN_THREAD_EVENT = "console.open-thread"
ARCHIVE_EVENT = "console.archive-thread"


def open_channel(console: "ConsoleService", operator_id: str, name: str, domain: str,
                 channel_id: str, standing: str) -> dict[str, Any]:
    """`console.open-channel`: a named domain container for threads."""
    grant = console.authorize(operator_id, ENFORCED_AUTHORITY[OPEN_CHANNEL_EVENT],
                              domain, OPEN_CHANNEL_EVENT, channel_id)
    return append.emit(console.record, "channel", channel_id, operator_id, {
        "node_id": console.node_id,
        "channel_id": channel_id, "name": name, "domain": domain,
        "opened_by": operator_id, "opened_at": console.stamp(), "standing": standing,
    }, OPEN_CHANNEL_EVENT, [grant])


def open_thread(console: "ConsoleService", operator_id: str, channel_id: str,
                title: str, pinned_address: str | None, pinned_digest: str | None,
                thread_id: str, standing: str) -> dict[str, Any]:
    """`console.open-thread`: a bounded conversation, optionally pinned to a record.

    The manifest declares `channel_exists` and this took the channel id on trust, so a
    thread could open into another node's channel, or into no channel at all.
    """
    if (pinned_address is None) != (pinned_digest is None):
        raise console.refusal(
            PinIncomplete("a pinned thread carries both an address and its digest"),
            OPEN_THREAD_EVENT, thread_id, operator_id)
    entries = console.record.reconstruct()
    grant = console.authorize(operator_id, ENFORCED_AUTHORITY[OPEN_THREAD_EVENT],
                              channel_id, OPEN_THREAD_EVENT, thread_id, entries)
    console.channel(channel_id, entries, OPEN_THREAD_EVENT, operator_id)
    return append.emit(console.record, "thread", thread_id, operator_id, {
        "node_id": console.node_id,
        "thread_id": thread_id, "channel_id": channel_id, "title": title,
        "opened_by": operator_id, "opened_at": console.stamp(), "lifecycle": "OPEN",
        "pinned_address": pinned_address, "pinned_digest": pinned_digest,
        "standing": standing,
    }, OPEN_THREAD_EVENT, [grant])


def archive_thread(console: "ConsoleService", operator_id: str, thread_id: str,
                   standing: str) -> dict[str, Any]:
    """`console.archive-thread`: posts stay readable; no new post may land in it."""
    entries = console.record.reconstruct()
    thread = console.held_thread(thread_id, entries, ARCHIVE_EVENT, operator_id)
    channel_id = thread["channel_id"]
    grant = console.authorize(operator_id, ENFORCED_AUTHORITY[ARCHIVE_EVENT],
                              channel_id, ARCHIVE_EVENT, thread_id, entries)
    return append.emit(console.record, "thread-lifecycle", thread_id, operator_id, {
        "node_id": console.node_id,
        "thread_id": thread_id, "channel_id": channel_id, "lifecycle": "ARCHIVED",
        "standing": standing,
    }, ARCHIVE_EVENT, [grant])
