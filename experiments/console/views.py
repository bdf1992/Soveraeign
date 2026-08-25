"""What the door can answer: one journal replay, folded into what a surface renders.

Everything here is derived from the journal and nothing here is authoritative.
`state` is the whole node in one read; `dry` decides whether looking also opens
the surface session, because a page that reported two entries on an untouched
node would be lying about the only number it has.

`door.py` owns what may be done; this owns what may be read.
"""

from __future__ import annotations

from typing import Any

import content
# `door` first, and not only for the lexical order: it puts the service packages on
# the path, so importing them above it fails when this module is reached first.
from door import NODE, ROOT, SURFACE_BINDING, console, operations
from soveraeign_console_service import ConsoleService, Projection, read_thread, session_context


def state(dry: bool = False) -> dict[str, Any]:
    """One replay, folded into everything the surface renders.

    `dry` reads without opening a surface session. Looking at an empty node would
    otherwise write the node's first two entries before the visitor had done
    anything, and a fresh surface that reports two entries on an untouched node is
    lying about the only number it has.
    """
    with console() as svc:
        return _state(svc, dry)


def _state(svc: ConsoleService, dry: bool = False) -> dict[str, Any]:
    # The session is ensured before the replay that produces the counts. Reading
    # first and opening after would report a journal two entries shorter than the
    # one this call just wrote.
    session = None if dry else _surface_session(svc, Projection(svc))
    entries = svc.record.reconstruct()
    projection = Projection(svc)
    people = {op[0]: {"operator_id": op[0], "actor_kind": op[1], "display": op[2], "role": op[3]}
              for op in content.OPERATORS}
    purposes = {domain: purpose for domain, _name, purpose in content.CHANNELS}

    posts = []
    for post in projection.posts:
        posts.append(dict(post, body=svc.body(post["content_address"]).decode("utf-8")))

    threads = []
    for thread in projection.thread.values():
        thread_posts = [p for p in posts if p["thread_id"] == thread["thread_id"]]
        threads.append({
            "thread_id": thread["thread_id"], "channel_id": thread["channel_id"],
            "title": thread["title"], "lifecycle": thread["lifecycle"],
            "pinned_address": thread.get("pinned_address"),
            "pinned_digest": thread.get("pinned_digest"),
            "opened_at": thread["opened_at"], "opened_by": thread["opened_by"],
            "post_count": len(thread_posts),
            "last_at": thread_posts[-1]["posted_at"] if thread_posts else thread["opened_at"],
            "actors": sorted({p["actor_id"] for p in thread_posts}),
        })

    channels = [dict(channel, purpose=purposes.get(channel["domain"], ""),
                     thread_count=sum(1 for t in threads if t["channel_id"] == channel["channel_id"]))
                for channel in projection.channel.values()]

    live = svc.grants()
    sessions = list(projection.session.values())
    acted = ({post["actor_id"] for post in posts}
             | {session["operator_id"] for session in sessions}
             | {channel["opened_by"] for channel in projection.channel.values()})
    return {
        "node_id": NODE,
        "channels": sorted(channels, key=lambda c: c["opened_at"]),
        "threads": sorted(threads, key=lambda t: t["opened_at"]),
        "posts": posts,
        # Who this node has actually seen act, separate from who the surface knows
        # how to name. On an empty node these are different lists, and showing the
        # roster as membership would populate a node nobody has used.
        "operators": [dict(person, acted=person["operator_id"] in acted)
                      for person in people.values()],
        "acted": sorted(acted),
        "grants": live,
        "sessions": sessions,
        "surface_session": session,
        "owner_actions": owner_actions(),
        "journal": _journal(entries),
        "counts": {"entries": len(entries), "channels": len(channels),
                   "threads": len(threads), "posts": len(posts), "grants": len(live),
                   "sessions": len(sessions)},
        "authoritative": False,
        "rebuilt_from": "record-service-journal",
    }


def owner_actions() -> list[str]:
    """The actions STATUS.yaml says the owner may take, read from STATUS.yaml.

    Hardcoding them here would let the surface offer a verb the record does not
    admit. Read with a narrow scan rather than a YAML parser: the repository's
    technical baseline keeps runtime dependencies out, and this needs one list.
    """
    text = (ROOT / "STATUS.yaml").read_text(encoding="utf-8")
    inside = False
    found: list[str] = []
    for line in text.splitlines():
        if line.strip() == "owner_actions:":
            inside = True
            continue
        if inside:
            stripped = line.strip()
            if stripped.startswith("- "):
                found.append(stripped[2:].strip())
            else:
                break
    return found


def _surface_session(svc: ConsoleService, projection: Projection) -> dict[str, Any]:
    """The open session this surface posts through, opening one if none is live.

    A surface that posted without a session would be writing unattributed records.
    Reusing an open one keeps a page reload from opening a session per visit.
    """
    mine = [s for s in projection.session.values()
            if s["operator_id"] == content.BDO and s["lifecycle"] == "OPEN"
            and s["binding_id"] == SURFACE_BINDING]
    if mine:
        return mine[-1]
    return svc.open_session(content.BDO, "HUMAN", SURFACE_BINDING)


def _journal(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The raw stream, newest last. Shown unsummarized; it is the proof the rest is real."""
    return [{"entry_id": e["entry_id"], "seq": e["seq"], "kind": e["kind"], "subject": e["subject"],
             "actor": e["actor"], "digest": e["entry_digest"],
             "record_kind": e["payload"].get("record_kind"),
             "operation": e["payload"].get("event"),
             "outcome": e["payload"].get("outcome"),
             "reason_code": (e["payload"].get("detail") or {}).get("reason_code"),
             "recorded_at": e.get("recorded_at")}
            for e in entries]


def _session_context(query: dict[str, str]) -> dict[str, Any]:
    with console() as svc:
        return session_context(svc, query.get("operator", content.BDO))


def _entry(query: dict[str, str]) -> dict[str, Any]:
    """Resolve one journal entry by id or by digest.

    A provenance chip that cannot be pulled on is decoration. This is what it
    pulls: the entry itself, verified on the way out, with the entry before it
    named so the chain is walkable rather than asserted.
    """
    wanted = query.get("id") or query.get("digest", "").replace("sha256:", "")
    with console() as svc:
        entries = svc.record.reconstruct()
        for index, entry in enumerate(entries):
            if wanted in (entry["entry_id"], entry["entry_digest"]):
                return {"entry": {k: v for k, v in entry.items() if k != "payload"},
                        "payload": entry["payload"],
                        "follows": entries[index - 1]["entry_id"] if index else "genesis",
                        "position": f"{index + 1} of {len(entries)}",
                        "chain_verified": True}
        for entry in entries:
            payload = entry["payload"]
            if payload.get("content_digest", "").endswith(wanted) or                payload.get("post_id") == wanted:
                return {"entry": {k: v for k, v in entry.items() if k != "payload"},
                        "payload": payload, "follows": entry["prev_digest"],
                        "position": "found by content digest", "chain_verified": True}
    raise KeyError(wanted)


def _thread(query: dict[str, str]) -> dict[str, Any]:
    with console() as svc:
        return read_thread(svc, query["thread"], SURFACE_BINDING)


READS = {
    "/api/state": lambda q: state(q.get("dry") == "1"),
    "/api/operations": lambda q: operations(),
    "/api/session-context": _session_context,
    "/api/thread": _thread,
    "/api/entry": _entry,
}



def last_receipt(svc: ConsoleService) -> dict[str, Any] | None:
    """The receipt the call just wrote. Read back out of the journal, not remembered."""
    for entry in reversed(svc.record.reconstruct()):
        if entry["kind"] == "RECEIPT":
            payload = entry["payload"]
            return {"entry_id": entry["entry_id"], "digest": entry["entry_digest"],
                    "subject": entry["subject"], "actor": entry["actor"],
                    "outcome": payload.get("outcome"), "event": payload.get("event"),
                    **{k: v for k, v in (payload.get("detail") or {}).items()
                       if k in ("operation_type", "effect_class", "authority_grant_ids",
                                "reason_code", "interface_id", "emitted_record_addresses")}}
    return None

