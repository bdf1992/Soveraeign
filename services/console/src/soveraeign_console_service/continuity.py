"""The console read path: projections rebuilt from the journal alone.

Everything here is derived. Nothing in this module reads console state that was
not replayed from the Record Service journal on this call, and nothing here can
be promoted to the authoritative record. Each returned view carries
`authoritative: false` and names the omissions it knows about, so a reader is
never left to assume a view was complete.

`session_context` is the cross-session piece: what one operator needs at the
start of a new session to continue work a previous session left open. It reads
the operator's last closed session, takes the read position that session pinned,
and reports what landed after it.
"""

from __future__ import annotations

from typing import Any

from soveraeign_console_service import contract
from soveraeign_console_service.core import ConsoleService

# What a fresh model instance must be able to discover before it can act. The
# AI-native reachability gate in `AI-NATIVE.md` is a discovery question, so the
# answer is a record rather than documentation.
OPERATIONS: tuple[dict[str, Any], ...] = (
    {"operation": "console.open-channel", "capability": "open-channel", "scope": "domain",
     "inputs": ["operator_id", "name", "domain"]},
    {"operation": "console.open-thread", "capability": "open-thread", "scope": "channel_id",
     "inputs": ["operator_id", "channel_id", "title", "pinned_address?", "pinned_digest?"]},
    {"operation": "console.archive-thread", "capability": "open-thread", "scope": "channel_id",
     "inputs": ["operator_id", "thread_id"]},
    {"operation": "console.publish-thread", "capability": "publish", "scope": "thread_id",
     "inputs": ["operator_id", "thread_id"]},
    {"operation": "console.withdraw-publication", "capability": "publish", "scope": "thread_id",
     "inputs": ["operator_id", "publication_id"]},
    {"operation": "console.list-publications", "capability": "read", "scope": "thread_id",
     "inputs": []},
    {"operation": "console.open-session", "capability": None, "scope": None,
     "inputs": ["operator_id", "actor_kind", "binding_id"]},
    {"operation": "console.close-session", "capability": None, "scope": None,
     "inputs": ["session_id"]},
    {"operation": "console.post", "capability": "post", "scope": "thread_id",
     "inputs": ["session_id", "thread_id", "body", "mentions?", "claims?", "proposal_id?"]},
)

# Each console record folds under one identity key. A lifecycle entry updates the
# record it names rather than replacing it, so `thread` and `thread-lifecycle`
# fold to the same thread.
_FOLDS = (
    ("channel", ("channel",), "channel_id"),
    ("thread", ("thread", "thread-lifecycle"), "thread_id"),
    ("session", ("operator-session", "operator-session-lifecycle"), "session_id"),
    ("publication", ("publication", "publication-lifecycle"), "publication_id"),
)


class Projection:
    """A rebuilt console read model. Derived, never authoritative."""

    def __init__(self, console: ConsoleService,
                 entries: list[dict[str, Any]] | None = None):
        self.channel: dict[str, dict[str, Any]] = {}
        self.thread: dict[str, dict[str, Any]] = {}
        self.session: dict[str, dict[str, Any]] = {}
        self.publication: dict[str, dict[str, Any]] = {}
        self.posts: list[dict[str, Any]] = []
        # `reconstruct` verifies every digest link before yielding, so a rewritten
        # history fails here instead of producing a plausible projection.
        for entry in entries if entries is not None else console.record.reconstruct():
            payload = entry["payload"]
            kind = payload.get("record_kind")
            for name, kinds, key in _FOLDS:
                if kind in kinds:
                    getattr(self, name).setdefault(payload[key], {}).update(payload)
            if kind == "post":
                self.posts.append(dict(payload, entry_id=entry["entry_id"]))

    def thread_posts(self, thread_id: str) -> list[dict[str, Any]]:
        """Posts in one thread, in append order."""
        return [post for post in self.posts if post["thread_id"] == thread_id]


def read_thread(console: ConsoleService, thread_id: str,
                binding_id: str | None = None, *,
                projection: Projection | None = None) -> dict[str, Any]:
    """Read one thread's posts in append order.

    The reading binding conditions presentation only. Two bindings asking for the
    same thread receive the same posts, in the same order, with the same addresses
    and digests; `read_through` records which surface asked.
    """
    projection = projection or Projection(console)
    if thread_id not in projection.thread:
        raise KeyError(thread_id)
    thread = projection.thread[thread_id]
    posts = [
        {"post_id": post["post_id"], "actor_id": post["actor_id"],
         "actor_kind": post["actor_kind"], "binding_id": post["binding_id"],
         "content_address": post["content_address"], "content_digest": post["content_digest"],
         "proposal_id": post["proposal_id"], "mentions": post["mentions"],
         "posted_at": post["posted_at"], "standing": post["standing"]}
        for post in projection.thread_posts(thread_id)
    ]
    return {"thread_id": thread_id, "title": thread["title"],
            "channel_id": thread["channel_id"], "lifecycle": thread["lifecycle"],
            "pinned_address": thread.get("pinned_address"),
            "pinned_digest": thread.get("pinned_digest"),
            "posts": posts, "read_through": binding_id,
            "omissions": [], "authoritative": False,
            "rebuilt_from": "record-service-journal"}


def published_threads(console: ConsoleService) -> dict[str, Any]:
    """The threads this node currently renders outwardly, rebuilt from the journal.

    This is the read `contracts/public-projection.schema.json` is built over. It is
    deliberately the same shape as every other console view - derived, never
    authoritative - because the outward surface is a projection like the operator's
    dashboard, not a second record (decisions/0039).

    A withdrawn publication is absent from `published` and named in `omissions`, so a
    reader can tell "never published" from "published and taken down" without being
    handed the journal.
    """
    records = contract.records(console.record.reconstruct())
    withdrawn = [record["thread_id"] for record in records["publications"]
                 if record["lifecycle"] == "WITHDRAWN"]
    return {"node_id": console.node_id,
            "published": contract.published_threads(records),
            "omissions": [f"{thread_id}: publication withdrawn" for thread_id in withdrawn],
            "authoritative": False,
            "rebuilt_from": "record-service-journal"}


def session_context(console: ConsoleService, operator_id: str) -> dict[str, Any]:
    """What this operator needs to resume across a session boundary.

    The read position comes from the `unread_cursor` the operator's last closed
    session pinned. Posts appended after that cursor are unseen by definition;
    posts by the operator themselves are excluded, because an operator reading
    their own last turn back is noise rather than continuity.
    """
    projection = Projection(console)
    sessions = [s for s in projection.session.values() if s["operator_id"] == operator_id]
    sessions.sort(key=lambda s: s["opened_at"])
    closed = [s for s in sessions if s["lifecycle"] == "CLOSED" and s.get("unread_cursor")]
    cursor = closed[-1]["unread_cursor"] if closed else None

    seen_cursor = cursor is None
    unseen: list[dict[str, Any]] = []
    for entry in console.record.reconstruct():
        if not seen_cursor:
            seen_cursor = entry["entry_digest"] == cursor
            continue
        payload = entry["payload"]
        if payload.get("record_kind") == "post" and payload["actor_id"] != operator_id:
            unseen.append({"post_id": payload["post_id"], "thread_id": payload["thread_id"],
                           "actor_id": payload["actor_id"], "actor_kind": payload["actor_kind"],
                           "content_address": payload["content_address"],
                           "content_digest": payload["content_digest"],
                           "posted_at": payload["posted_at"],
                           "mentions_you": operator_id in payload["mentions"]})

    open_threads = [
        {"thread_id": thread["thread_id"], "title": thread["title"],
         "channel_id": thread["channel_id"],
         "pinned_address": thread.get("pinned_address"),
         "post_count": len(projection.thread_posts(thread["thread_id"]))}
        for thread in projection.thread.values() if thread["lifecycle"] == "OPEN"
    ]
    omissions = ([] if cursor else
                 [{"source": "unread_cursor",
                   "reason": "this operator has no closed session, so every post reads as unseen"}])
    return {"operator_id": operator_id, "cursor": cursor,
            "prior_sessions": [{"session_id": s["session_id"], "binding_id": s["binding_id"],
                                "actor_kind": s["actor_kind"], "opened_at": s["opened_at"],
                                "closed_at": s.get("closed_at"), "lifecycle": s["lifecycle"]}
                               for s in sessions[-5:]],
            "open_threads": sorted(open_threads, key=lambda t: t["thread_id"]),
            "unseen_posts": unseen, "omissions": omissions,
            "authoritative": False, "rebuilt_from": "record-service-journal"}
