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

Discovery used to live here as a hand-written tuple of nine console operations.
It now comes from the capability projection - see `discovery.py` - because a
second list beside the map answers confidently and is wrong the first time an
operation moves (Bdo, 2026-08-24; `decisions/0053`).
"""

from __future__ import annotations

from typing import Any

from soveraeign_console_service import contract, reads
from soveraeign_console_service.authority import ENFORCED_AUTHORITY
from soveraeign_console_service.core import ConsoleService
from soveraeign_console_service.refusals import UnknownRecord

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
    """A rebuilt console read model over one node's records. Derived, never authoritative.

    Every fold here is narrowed to the node this console serves. A listing has no
    single subject to refuse about, so it filters rather than refusing: another
    node's channels, threads, posts and publications are not in the answer at all.

    Without that filter, binding a grant to its minting node bought nothing on the
    read path. A caller refused `node:local`'s permits office opens its own under any
    other name - names are unbounded - grants itself `read:thread` there, and reads
    `node:local`'s threads and post bytes with it. An independent witness walked that
    through the CLI on 2026-08-25.
    """

    def __init__(self, console: ConsoleService,
                 entries: list[dict[str, Any]] | None = None):
        self.channel: dict[str, dict[str, Any]] = {}
        self.thread: dict[str, dict[str, Any]] = {}
        self.session: dict[str, dict[str, Any]] = {}
        self.publication: dict[str, dict[str, Any]] = {}
        self.posts: list[dict[str, Any]] = []
        # `reconstruct` verifies every digest link before yielding, so a rewritten
        # history fails here instead of producing a plausible projection.
        replay = entries if entries is not None else console.record.reconstruct()
        #: What this fold dropped, by record kind. A view that silently omits a
        #: record breaks the promise the module docstring makes, and the drop is not
        #: hypothetical: a record written before console records carried a node
        #: belongs to no node and is filtered by the same rule a peer's is.
        self.omitted: dict[str, int] = {}
        folded = {kind for _, kinds, _ in _FOLDS for kind in kinds} | {"post"}
        for entry in replay:
            payload = entry["payload"]
            kind = payload.get("record_kind")
            if kind in folded and payload.get("node_id") != console.node_id:
                self.omitted[kind] = self.omitted.get(kind, 0) + 1
        for entry in reads.local(replay, console.node_id):
            payload = entry["payload"]
            kind = payload.get("record_kind")
            for name, kinds, key in _FOLDS:
                if kind in kinds:
                    getattr(self, name).setdefault(payload[key], {}).update(payload)
            if kind == "post":
                self.posts.append(dict(payload, entry_id=entry["entry_id"]))

    def omissions(self) -> list[str]:
        """What this projection could not show, in the words a reader needs.

        `continuity.py` promises every view names its omissions. The node filter that
        closed the cross-node read added a way to drop a record without saying so.
        """
        return [f"{count} {kind} record(s) omitted: not this node's to show"
                for kind, count in sorted(self.omitted.items())]

    def thread_posts(self, thread_id: str) -> list[dict[str, Any]]:
        """Posts in one thread, in append order."""
        return [post for post in self.posts if post["thread_id"] == thread_id]


def read_thread(console: ConsoleService, thread_id: str,
                binding_id: str | None = None, *, operator_id: str,
                projection: Projection | None = None) -> dict[str, Any]:
    """`console.read-thread`: one thread's posts in append order, for an admitted reader.

    The reading binding conditions presentation only. Two bindings asking for the
    same thread receive the same posts, in the same order, with the same addresses
    and digests; `read_through` records which surface asked.

    `operator_id` is keyword-only and has no default. Before 2026-08-25 this read
    checked nothing, so a reader who happened to hold the service object read any
    thread on the node; the Gateway checked `read:thread` for the routed path and
    the direct and CLI paths went unguarded. The check is here rather than at the
    route so all three paths cross it, and the routed path repeats a check it has
    already passed rather than trusting that it did.
    """
    console.authorize(operator_id, ENFORCED_AUTHORITY["console.read-thread"], thread_id,
                      "console.read-thread", thread_id)
    projection = projection or Projection(console)
    if thread_id not in projection.thread:
        # Either no such thread, or one this node does not own: `Projection` folds
        # only this node's records, so a peer's thread is absent rather than hidden.
        raise UnknownRecord(thread_id)
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
            "omissions": projection.omissions(), "authoritative": False,
            "rebuilt_from": "record-service-journal"}


def published_threads(console: ConsoleService, *, operator_id: str) -> dict[str, Any]:
    """`console.list-publications`: the threads this node renders outwardly.

    This is the read `contracts/public-projection.schema.json` is built over. It is
    deliberately the same shape as every other console view - derived, never
    authoritative - because the outward surface is a projection like the operator's
    dashboard, not a second record (decisions/0039).

    A withdrawn publication is absent from `published` and named in `omissions`, so a
    reader can tell "never published" from "published and taken down" without being
    handed the journal.

    This is every published thread on the node rather than one thread, so the
    `read:thread` grant it checks is scoped to the node. Before 2026-08-25 it
    checked nothing and it is reachable over the CLI, so the outward surface of the
    node was readable by anyone who could run the command.
    """
    entries = console.record.reconstruct()
    console.authorize(operator_id, ENFORCED_AUTHORITY["console.list-publications"],
                      console.node_id, "console.list-publications", console.node_id,
                      entries)
    records = contract.local_records(contract.records(entries), console.node_id)
    withdrawn = [record["thread_id"] for record in records["publications"]
                 if record["lifecycle"] == "WITHDRAWN"]
    everything = contract.records(entries)
    elsewhere = sum(len(rows) - len(records[group]) for group, rows in everything.items())
    return {"node_id": console.node_id,
            "published": contract.published_threads(records),
            "omissions": [f"{thread_id}: publication withdrawn" for thread_id in withdrawn]
            + ([f"{elsewhere} record(s) omitted: not this node's to show"]
               if elsewhere else []),
            "authoritative": False,
            "rebuilt_from": "record-service-journal"}


def session_context(console: ConsoleService, reader_id: str,
                    operator_id: str | None = None) -> dict[str, Any]:
    """`console.session-context`: what an operator needs to resume across a session.

    The read position comes from the `unread_cursor` the operator's last closed
    session pinned. Posts appended after that cursor are unseen by definition;
    posts by the operator themselves are excluded, because an operator reading
    their own last turn back is noise rather than continuity.

    `reader_id` is who is asking and is what the `read:session` grant is checked
    against; `operator_id` is whose continuity is being read and defaults to the
    reader, the ordinary case of resuming your own work. The two are separate
    arguments because a check made against the subject is not a check: every
    operator holds `read:session` over itself, so falling back to the subject would
    admit any caller who named one. Before 2026-08-25 this checked nothing at all
    and handed whoever asked everything that landed while an operator was away.
    """
    subject = operator_id or reader_id
    console.authorize(reader_id, ENFORCED_AUTHORITY["console.session-context"],
                      subject, "console.session-context", subject)
    operator_id = subject
    projection = Projection(console)
    sessions = [s for s in projection.session.values() if s["operator_id"] == operator_id]
    sessions.sort(key=lambda s: s["opened_at"])
    closed = [s for s in sessions if s["lifecycle"] == "CLOSED" and s.get("unread_cursor")]
    cursor = closed[-1]["unread_cursor"] if closed else None

    seen_cursor = cursor is None
    unseen: list[dict[str, Any]] = []
    # The whole journal, because the cursor is a position in the whole journal: a
    # closed session pins `record.head()`, which is usually a receipt and carries no
    # node. Filtering the walk itself would step past the cursor and report nothing
    # unseen. The node test belongs on what is collected, not on what is counted.
    for entry in console.record.reconstruct():
        if not seen_cursor:
            seen_cursor = entry["entry_digest"] == cursor
            continue
        payload = entry["payload"]
        if payload.get("node_id") != console.node_id:
            continue
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
    omissions.extend({"source": "node_scope", "reason": line}
                     for line in projection.omissions())
    return {"operator_id": operator_id, "cursor": cursor,
            "prior_sessions": [{"session_id": s["session_id"], "binding_id": s["binding_id"],
                                "actor_kind": s["actor_kind"], "opened_at": s["opened_at"],
                                "closed_at": s.get("closed_at"), "lifecycle": s["lifecycle"]}
                               for s in sessions[-5:]],
            "open_threads": sorted(open_threads, key=lambda t: t["thread_id"]),
            "unseen_posts": unseen, "omissions": omissions,
            "authoritative": False, "rebuilt_from": "record-service-journal"}
