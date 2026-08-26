"""The operator-session lifecycle: `OPEN -> CLOSED`, and what a close pins.

`core.py` owns the threaded record path - channels, threads, posts. A session is
not part of that path; it is the boundary around one operator's continuity, and
`continuity.py` reads what a close left behind rather than what a post did. So the
two transitions that move a session live here, next to each other, the way
`authority.py` owns the grant record's lifecycle.

Both are guarded. `open:session` and `close:session` scope to the session's
operator rather than to a session id: a grant scoped to one session would expire
the moment it became useful, and closing somebody else's session is then the same
check over a different scope rather than a second rule.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from soveraeign_console_service import append
from soveraeign_console_service.authority import ENFORCED_AUTHORITY

if TYPE_CHECKING:  # pragma: no cover - broken at runtime; core imports this module
    from soveraeign_console_service.core import ConsoleService

ACTOR_KINDS = ("HUMAN", "MODEL")
OPEN_EVENT = "console.open-session"
CLOSE_EVENT = "console.close-session"


def open_session(console: "ConsoleService", operator_id: str, actor_kind: str,
                 binding_id: str, session_id: str, standing: str) -> dict[str, Any]:
    """`console.open-session`: one operator's continuity through a named binding.

    A binding realizes an interface and grants no authority. It is carried so a
    later reader can see which surface a post arrived through.
    """
    if actor_kind not in ACTOR_KINDS:
        raise ValueError(f"unknown actor_kind {actor_kind!r}")
    grant = console.authorize(operator_id, ENFORCED_AUTHORITY[OPEN_EVENT], operator_id,
                              OPEN_EVENT, session_id)
    return append.emit(console.record, "operator-session", session_id, operator_id, {
        "node_id": console.node_id,
        "session_id": session_id, "operator_id": operator_id,
        "actor_kind": actor_kind, "binding_id": binding_id,
        "opened_at": console.stamp(), "closed_at": None, "lifecycle": "OPEN",
        "active_thread_id": None, "unread_cursor": None,
        "standing": standing,
    }, OPEN_EVENT, [grant])


def close_session(console: "ConsoleService", operator_id: str, session_id: str,
                  standing: str) -> dict[str, Any]:
    """`console.close-session`: close a session and pin its read position.

    `operator_id` is who is closing it, which is not always whose session it is, and
    it is the actor the entry and the receipt carry. The record's own `operator_id`
    field stays the session's owner: a close by somebody else must not read as the
    owner having closed it. Before 2026-08-25 this took the session alone, admitted
    any caller, and attributed every close to the owner.
    """
    entries = console.record.reconstruct()
    # The grant's scope is this session's operator, which cannot be known without
    # reading the session, so an unearned caller gets the missing-record answer.
    session = console.held_session(session_id, entries, CLOSE_EVENT, operator_id)
    grant = console.authorize(operator_id, ENFORCED_AUTHORITY[CLOSE_EVENT],
                              session["operator_id"], CLOSE_EVENT, session_id, entries)
    return append.emit(console.record, "operator-session-lifecycle", session_id,
                       operator_id, {
        "node_id": console.node_id,
        "session_id": session_id, "operator_id": session["operator_id"],
        "actor_kind": session["actor_kind"], "binding_id": session["binding_id"],
        "lifecycle": "CLOSED", "closed_at": console.stamp(),
        "unread_cursor": console.record.head(), "standing": standing,
    }, CLOSE_EVENT, [grant])
