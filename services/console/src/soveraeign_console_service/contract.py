"""Project journal payloads into the record shapes `contracts/` declares.

A journal entry carries more than a console record does: the kind that told the
folder what it was, the entry id, the digest of the entry before it. Those belong
to the journal, not to the record, and `contracts/post.schema.json` and its
siblings close their objects against exactly that kind of leakage.

So the declared record is a projection, assembled here and validated against the
schema files by `tests/test_contract_shapes.py`. Assembling it is not cosmetic:
`post.schema.json` requires a `receipt_id`, and a post cannot carry the id of a
receipt that is written after it. The link runs the other way - the receipt names
the event in `emitted_record_addresses` - so the record is only whole once both
halves are read back together, which is the honest shape of an append-only store.
"""

from __future__ import annotations

from typing import Any

from soveraeign_console_service import reads

CHANNEL_FIELDS = ("node_id", "channel_id", "name", "domain", "opened_by", "opened_at",
                  "standing")
THREAD_FIELDS = ("node_id", "thread_id", "channel_id", "title", "opened_by", "opened_at",
                 "lifecycle", "pinned_address", "pinned_digest", "standing")
SESSION_FIELDS = ("node_id", "session_id", "operator_id", "principal_id", "actor_kind",
                  "binding_id", "opened_at", "closed_at", "lifecycle", "active_thread_id",
                  "unread_cursor", "standing")
POST_FIELDS = ("node_id", "post_id", "thread_id", "actor_id", "actor_kind", "session_id",
               "binding_id", "principal_id", "content_address", "content_digest", "mentions",
               "proposal_id", "posted_at", "receipt_id", "standing")
PUBLICATION_FIELDS = ("node_id", "publication_id", "thread_id", "visibility", "lifecycle",
                      "published_by", "published_at", "withdrawn_at", "standing")


def _project(payload: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    """Take exactly the declared fields, defaulting an absent optional to null."""
    return {field: payload.get(field) for field in fields}


def channel_record(payload: dict[str, Any]) -> dict[str, Any]:
    """One channel as `contracts/channel.schema.json` declares it."""
    return _project(payload, CHANNEL_FIELDS)


def thread_record(payload: dict[str, Any]) -> dict[str, Any]:
    """One thread as `contracts/thread.schema.json` declares it."""
    return _project(payload, THREAD_FIELDS)


def session_record(payload: dict[str, Any]) -> dict[str, Any]:
    """One operator session as `contracts/operator-session.schema.json` declares it."""
    return _project(payload, SESSION_FIELDS)


def post_record(payload: dict[str, Any], receipt_id: str) -> dict[str, Any]:
    """One post as `contracts/post.schema.json` declares it, joined to its receipt."""
    return _project(dict(payload, receipt_id=receipt_id), POST_FIELDS)


def publication_record(payload: dict[str, Any]) -> dict[str, Any]:
    """One publication as `contracts/publication.schema.json` declares it."""
    return _project(payload, PUBLICATION_FIELDS)


def published_threads(projected: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """The threads currently marked public, as the outward surface would render them.

    A withdrawn publication is absent from this list and still present in the journal.
    That difference is the whole point of withdrawing by appending: the outward view
    stops showing a thread without the record of it having been shown going away.
    """
    threads = {record["thread_id"]: record for record in projected["threads"]}
    published: list[dict[str, Any]] = []
    for record in projected["publications"]:
        if record["lifecycle"] != "PUBLISHED":
            continue
        thread = threads.get(record["thread_id"])
        if thread is None:
            continue
        published.append({"thread_id": record["thread_id"], "node_id": thread["node_id"],
                          "published_by": record["published_by"],
                          "published_at": record["published_at"]})
    return sorted(published, key=lambda record: record["thread_id"])


def local_records(projected: dict[str, list[dict[str, Any]]],
                  node_id: str) -> dict[str, list[dict[str, Any]]]:
    """One node's view of a projection, for a caller that must not see a peer's records.

    Applied after `records` rather than inside it, so `foreign_records` still reads a
    projection that can contain a contradiction to report.
    """
    return {group: [record for record in rows if record.get("node_id") == node_id]
            for group, rows in projected.items()}


def foreign_records(projected: dict[str, list[dict[str, Any]]], node_id: str) -> list[str]:
    """Every projected record that does not belong to ``node_id``.

    A journal that carries records from two nodes is not corrupt; once a crossing
    exists it is the expected shape (decisions/0039). What would be a defect is
    presenting a peer's record as this node's own, so the contradiction is reported
    here rather than raised. A record whose ``node_id`` disagrees with its container's
    is named too - a thread against its channel, a post against its thread: one of the
    two is wrong and neither is authoritative over the other.
    """
    by_channel = {record["channel_id"]: record for record in projected["channels"]}
    by_thread = {record["thread_id"]: record for record in projected["threads"]}
    foreign: list[str] = []
    for record in projected["channels"]:
        if record["node_id"] != node_id:
            foreign.append(f"channel {record['channel_id']}: belongs to {record['node_id']}")
    for record in projected["threads"]:
        if record["node_id"] != node_id:
            foreign.append(f"thread {record['thread_id']}: belongs to {record['node_id']}")
        channel = by_channel.get(record["channel_id"])
        if channel is not None and channel["node_id"] != record["node_id"]:
            foreign.append(
                f"thread {record['thread_id']}: claims node {record['node_id']} but its "
                f"channel {record['channel_id']} claims {channel['node_id']}")
    # Posts and sessions were invisible here until 2026-08-25: they carried a node on
    # the journal record and the declared projection dropped it, so the one detector
    # this repository has for the contradiction could not see the two record kinds a
    # foreign write actually produces.
    for record in projected["operator_sessions"]:
        if record["node_id"] != node_id:
            foreign.append(
                f"operator session {record['session_id']}: belongs to {record['node_id']}")
    for record in projected["posts"]:
        if record["node_id"] != node_id:
            foreign.append(f"post {record['post_id']}: belongs to {record['node_id']}")
        thread = by_thread.get(record["thread_id"])
        if thread is not None and thread["node_id"] != record["node_id"]:
            foreign.append(
                f"post {record['post_id']}: claims node {record['node_id']} but its "
                f"thread {record['thread_id']} claims {thread['node_id']}")
    return foreign


def receipt_index(entries: list[dict[str, Any]]) -> dict[str, str]:
    """Map each emitted record address to the receipt that committed it.

    A post whose event address is absent from this index has no receipt, which is
    a declared defeating case rather than a presentation problem: a binding that
    wrote a record without one bypassed the transition.
    """
    index: dict[str, str] = {}
    for entry in entries:
        if entry["kind"] != "RECEIPT" or entry["payload"]["outcome"] != "COMMITTED":
            continue
        for address in entry["payload"]["detail"].get("emitted_record_addresses", []):
            index[address] = entry["entry_id"]
    return index


def records(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Every console record in the journal, in declared shape, in append order.

    `entries` must come from `RecordService.reconstruct`, which verifies the digest
    chain first. Passing an unverified read would project a rewritten history as if
    it were sound.

    Deliberately unfiltered. `foreign_records` is the one detector this repository
    has for a peer's record presented as this node's own, and it reads this output;
    narrowing here on 2026-08-25 made it structurally unable to fire in every
    production path, so the same change widened a verifier and blinded it. A caller
    that wants one node's view narrows afterwards with `local_records`.
    """
    receipts = receipt_index(entries)
    folded: dict[str, dict[str, dict[str, Any]]] = {"channel": {}, "thread": {}, "session": {},
                                                    "publication": {}}
    posts: list[dict[str, Any]] = []
    for entry in entries:
        payload = entry["payload"]
        kind = payload.get("record_kind")
        if kind == "channel":
            folded["channel"][payload["channel_id"]] = dict(payload)
        elif kind in ("thread", "thread-lifecycle"):
            folded["thread"].setdefault(payload["thread_id"], {}).update(payload)
        elif kind in ("publication", "publication-lifecycle"):
            folded["publication"].setdefault(payload["publication_id"], {}).update(payload)
        elif kind in ("operator-session", "operator-session-lifecycle"):
            folded["session"].setdefault(payload["session_id"], {}).update(payload)
        elif kind == "post":
            posts.append(post_record(payload, receipts.get(entry["entry_id"], "")))
    return {
        "channels": [channel_record(record) for record in folded["channel"].values()],
        "threads": [thread_record(record) for record in folded["thread"].values()],
        "operator_sessions": [session_record(record) for record in folded["session"].values()],
        "publications": [publication_record(record)
                         for record in folded["publication"].values()],
        "posts": posts,
    }
