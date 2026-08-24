"""A local door onto the Console Service, for a human gesture and a model call alike.

There is one dispatch path. `GET /api/operations` returns the same discovery
answer the CLI's `operations` command gives, and `POST /api/call` invokes any of
them by name. The page builds its controls from that list rather than hardcoding
buttons, so an operation added to the service reaches the surface without the
page being edited, and a model driving this door uses exactly the calls a click
uses.

A refusal returns HTTP 409 with its stable `reason_code` and the receipt it
wrote. Nothing here decides anything: every commit and every refusal is the
Console Service's, appended to the journal before this process answers.

Local only, no authentication, no external effects. It binds 127.0.0.1 and
refuses anything else, because a console that quietly listened on a network
interface would be an external-world effect nobody admitted.
"""

from __future__ import annotations

from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterator
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "services" / "console" / "src"))
sys.path.insert(0, str(ROOT / "services" / "record" / "src"))
sys.path.insert(0, str(HERE))

from soveraeign_console_service import (  # noqa: E402
    ConsoleRefusal,
    ConsoleService,
    Projection,
    read_thread,
    session_context,
)
from soveraeign_console_service.continuity import OPERATIONS  # noqa: E402
from soveraeign_record_service import RecordService  # noqa: E402

import content  # noqa: E402

STORE = ROOT / ".local" / "console"
NODE = "node:local"
HOST, PORT = "127.0.0.1", 8787
SURFACE_BINDING = "binding:console-surface"


@contextmanager
def console() -> Iterator[ConsoleService]:
    """A service over the journal for the length of one call, then closed.

    State lives in the journal, not in this process, so nothing is kept between
    calls. The connection is closed on the way out: a handle held open per request
    would pile up until the store could not be replaced, which is exactly how the
    seeder first failed on Windows.
    """
    record = RecordService(STORE / "journal")
    try:
        yield ConsoleService(record, STORE, NODE)
    finally:
        record.db.close()


# ---- the operation registry the surface renders itself from -----------------

def _post(svc: ConsoleService, i: dict[str, Any]) -> dict[str, Any]:
    return svc.post(i["session_id"], i["thread_id"], i["body"].encode("utf-8"),
                    i.get("mentions", ()), bool(i.get("claims")), i.get("proposal_id"))


CALLS = {
    "console.open-channel": lambda s, i: s.open_channel(i["operator_id"], i["name"], i["domain"]),
    "console.open-thread": lambda s, i: s.open_thread(i["operator_id"], i["channel_id"],
                                                      i["title"], i.get("pinned_address"),
                                                      i.get("pinned_digest")),
    "console.archive-thread": lambda s, i: s.archive_thread(i["operator_id"], i["thread_id"]),
    "console.publish-thread": lambda s, i: s.publish_thread(i["operator_id"], i["thread_id"]),
    "console.withdraw-publication": lambda s, i: s.withdraw_publication(i["operator_id"],
                                                                        i["publication_id"]),
    "console.open-session": lambda s, i: s.open_session(i["operator_id"], i["actor_kind"],
                                                        i["binding_id"]),
    "console.close-session": lambda s, i: s.close_session(i["session_id"]),
    "console.post": _post,
    "console.grant": lambda s, i: s.grant(i["operator_id"], i["capability"], i["scope"]),
}


def operations() -> dict[str, Any]:
    """What may be done here, and what each operation requires.

    The same answer a model gets from the CLI. `grant` is added because this door
    exposes it and the CLI list does not; saying so is cheaper than a surface that
    can do something its own declaration denies.
    """
    declared = [dict(op, callable_here=op["operation"] in CALLS) for op in OPERATIONS]
    declared.append({"operation": "console.grant", "capability": None, "scope": None,
                     "inputs": ["operator_id", "capability", "scope"], "callable_here": True})
    return {"node_id": NODE, "operations": declared, "entry_standing": "RECORDED",
            "note": "a console record never enters above RECORDED",
            "call": {"method": "POST", "path": "/api/call",
                     "body": {"operation": "<name>", "inputs": {}},
                     "refusal": "HTTP 409 with reason_code and the receipt it wrote"}}


# ---- read paths -------------------------------------------------------------

def state() -> dict[str, Any]:
    """One replay, folded into everything the surface renders."""
    with console() as svc:
        return _state(svc)


def _state(svc: ConsoleService) -> dict[str, Any]:
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
    return {
        "node_id": NODE,
        "channels": sorted(channels, key=lambda c: c["opened_at"]),
        "threads": sorted(threads, key=lambda t: t["opened_at"]),
        "posts": posts,
        "operators": list(people.values()),
        "grants": live,
        "sessions": sessions,
        "surface_session": _surface_session(svc, projection),
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
    "/api/state": lambda q: state(),
    "/api/operations": lambda q: operations(),
    "/api/session-context": _session_context,
    "/api/thread": _thread,
    "/api/entry": _entry,
}


# ---- http -------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    """One dispatcher. Reads are declared in READS, writes in CALLS."""

    server_version = "soveraeign-console-surface"

    def do_GET(self) -> None:  # noqa: N802 - http.server's interface
        path, _, query = self.path.partition("?")
        params = dict(pair.split("=", 1) for pair in query.split("&") if "=" in pair)
        if path in READS:
            try:
                return self._json(READS[path](params))
            except KeyError as error:
                return self._json({"error": "unknown", "detail": str(error)}, 404)
        if path in ("/", "/index.html"):
            return self._page(_latest_freeze())
        freeze = HERE / f"app.{path.lstrip('/')}.html"
        if freeze.exists():
            return self._page(freeze)
        return self._json({"error": "not_found", "freezes": _freezes()}, 404)

    def do_POST(self) -> None:  # noqa: N802 - http.server's interface
        if self.path != "/api/call":
            return self._json({"error": "not_found"}, 404)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            request = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError as error:
            return self._json({"error": "bad_json", "detail": str(error)}, 400)
        name = request.get("operation")
        if name not in CALLS:
            return self._json({"error": "unknown_operation", "operation": name,
                               "available": sorted(CALLS)}, 404)
        with console() as svc:
            try:
                record = CALLS[name](svc, request.get("inputs") or {})
            except ConsoleRefusal as refusal:
                # The service already wrote a REFUSED receipt before raising.
                return self._json({"outcome": "REFUSED", "operation": name,
                                   "reason_code": refusal.reason_code, "message": str(refusal),
                                   "receipt": _last_receipt(svc)}, 409)
            except KeyError as missing:
                return self._json({"error": "missing_input", "input": str(missing)}, 400)
            return self._json({"outcome": "COMMITTED", "operation": name, "record": record,
                               "receipt": _last_receipt(svc)})

    def _json(self, payload: Any, code: int = 200) -> None:
        body = json.dumps(payload, indent=2, sort_keys=True, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _page(self, path: Path) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        """One line per call, so what the surface did is visible without a debugger."""
        sys.stderr.write(f"  {args[0]}\n" if args else "")


def _last_receipt(svc: ConsoleService) -> dict[str, Any] | None:
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


def _freezes() -> list[str]:
    return sorted(p.stem.split(".", 1)[1] for p in HERE.glob("app.v*.html"))


def _latest_freeze() -> Path:
    names = _freezes()
    if not names:
        raise SystemExit("no app.v*.html in experiments/console")
    return HERE / f"app.{names[-1]}.html"


def main() -> None:
    if not (STORE / "journal").exists():
        raise SystemExit("no console store; run: python experiments/console/seed.py")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"console surface on http://{HOST}:{PORT}")
    print(f"freezes: {', '.join('/' + name for name in _freezes()) or 'none yet'}")
    print(f"store:   {STORE}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
