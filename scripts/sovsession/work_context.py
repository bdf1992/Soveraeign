"""Concern-scoped session commands split out of commands.py."""

from __future__ import annotations

from pathlib import Path
import json
import os

from sovsession import brief, concerns, principals, store


def register(root: Path, directory: Path, name: str, tree: str, args) -> int:
    fields = concerns.session_fields(name, args.concern, args.source_session,
                                     args.sources, args.queues)
    existing = store.sessions(directory).get(name)
    defect = concerns.binding_defect(existing, fields["concern"])
    if defect:
        payload = {"decision": "REFUSED", "reason": defect, "session": name}
        print(json.dumps(payload, indent=2, sort_keys=True) if args.as_json else defect)
        return 1
    claim = principals.resolve(root, name)
    store.append(directory, store.SESSIONS_LOG, {
        "event": "register", "session": name,
        "principal": claim["principal"], "verification": claim["verification"],
        "pid": int(os.environ.get("CLAUDE_PID", 0) or 0),
        "tree": tree, "branch": brief.branch_of(root), "intent": args.intent or "",
        **fields,
    })
    data = brief.collect(root, directory, name, tree)
    print(json.dumps(data, indent=2, sort_keys=True) if args.as_json else brief.render(data))
    return 0


def route(directory: Path, name: str, args) -> int:
    record = store.sessions(directory).get(name) or {}
    if not record.get("registered"):
        message = "SESSION_NOT_REGISTERED: register before routing a concern crossing"
        print(json.dumps({"decision": "REFUSED", "reason": message}, indent=2)
              if args.as_json else message)
        return 1
    event = concerns.record_route(directory, record, args.to_concern, args.sources,
                                  args.queue or "", args.disposition or "PENDING")
    print(json.dumps(event, indent=2, sort_keys=True) if args.as_json
          else f"{event['route_id']}: {event['source_concern']} -> {event['destination_concern']}")
    return 0


def console(root: Path, directory: Path, name: str, tree: str, args) -> int:
    data = brief.collect(root, directory, name, tree)
    print(json.dumps(data, indent=2, sort_keys=True)
          if args.as_json else brief.render_console(data))
    return 0
