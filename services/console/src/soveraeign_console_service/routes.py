"""Service-owned route for the declared Console thread read.

The Gateway checks actor kind and live authority. This adapter checks the
Console-owned session and object preconditions, rebuilds the existing projection
from the Record journal, and returns one Console-owned terminal receipt. It does
not open sessions, mutate Thread/Post objects, or turn the projection into authority.
"""

from __future__ import annotations

import json
import re
from hashlib import sha256
from typing import Any

from soveraeign_console_service.continuity import Projection, read_thread
from soveraeign_console_service.core import ConsoleService

EFFECT_CLASS = "RECORD_LOCAL"
EVENT = "console.read-thread"
IDENTITY = re.compile(r"^(?P<kind>session|thread)_[0-9a-f]{16}$")


class ConsoleRoutes:
    """Expose exact Console arguments without re-performing Gateway authority."""

    OPERATIONS = ("read-thread",)
    ARGUMENTS = {
        "read-thread": {"required": ("thread_id", "session_id"), "optional": ()},
    }

    def __init__(self, service: ConsoleService) -> None:
        self.service = service

    @classmethod
    def operation_ids(cls) -> tuple[str, ...]:
        """Exact operation census without reading Console state."""
        return cls.OPERATIONS

    @classmethod
    def argument_contract(cls, operation: str) -> dict[str, tuple[str, ...]]:
        """Return the service-owned argument names for one operation."""
        return cls.ARGUMENTS[operation]

    def call(self, operation: str, arguments: dict[str, Any], actor: str) -> dict[str, Any]:
        """Invoke one declared Console route and return its terminal receipt."""
        if operation != "read-thread":
            raise KeyError(f"console route {operation!r} is not bound")
        return self._read_thread(arguments, actor)

    def _receipt(self, outcome: str, actor: str, subject: str,
                 detail: dict[str, Any]) -> dict[str, Any]:
        return self.service.record.receipt(
            outcome, EVENT, subject, actor,
            {"effect_class": EFFECT_CLASS, "operation_type": EVENT, **detail},
        )

    def _refuse(self, actor: str, subject: str, reason_code: str) -> dict[str, Any]:
        return self._receipt("REFUSED", actor, subject, {"reason_code": reason_code})

    def _read_thread(self, arguments: dict[str, Any], actor: str) -> dict[str, Any]:
        required = {"thread_id", "session_id"}
        if set(arguments) != required or any(
                not isinstance(arguments.get(name), str) for name in required):
            return self._refuse(actor, "console-thread", "MALFORMED_IDENTITY")
        thread_id, session_id = arguments["thread_id"], arguments["session_id"]
        thread_match = IDENTITY.fullmatch(thread_id)
        session_match = IDENTITY.fullmatch(session_id)
        if (thread_match is None or thread_match.group("kind") != "thread"
                or session_match is None or session_match.group("kind") != "session"):
            return self._refuse(actor, thread_id or "console-thread", "MALFORMED_IDENTITY")

        entries = self.service.record.reconstruct()
        projection = Projection(self.service, entries)
        session = projection.session.get(session_id)
        if session is None:
            return self._refuse(actor, thread_id, "SESSION_NOT_LIVE")
        if session.get("lifecycle") != "OPEN":
            return self._refuse(actor, thread_id, "SESSION_NOT_LIVE")
        if session.get("operator_id") != actor:
            return self._refuse(actor, thread_id, "ACTOR_ATTRIBUTION_MISMATCH")
        if thread_id not in projection.thread:
            return self._refuse(actor, thread_id, "THREAD_UNKNOWN")

        snapshot_digest = self.service.record.head()
        reading = read_thread(
            self.service, thread_id, str(session.get("binding_id")), projection=projection)
        object_record = _object_record(entries, reading, snapshot_digest)
        return self._receipt("COMMITTED", actor, thread_id, {
            "reason_code": None,
            "commit_semantics": "DERIVED",
            "standing_effect": "NONE",
            "object_record": object_record,
        })


def _source_record(entry: dict[str, Any]) -> dict[str, str]:
    payload = entry["payload"]
    return {
        "address": entry["entry_id"],
        "digest": entry["entry_digest"],
        "role": str(payload.get("record_kind", "journal-entry")),
    }


def _receipt_refs(entries: list[dict[str, Any]], addresses: set[str]) -> list[str]:
    refs = []
    for entry in entries:
        if entry["kind"] != "RECEIPT":
            continue
        emitted = entry["payload"].get("detail", {}).get("emitted_record_addresses", [])
        if addresses.intersection(emitted):
            refs.append(entry["entry_id"])
    return refs


def _object_record(entries: list[dict[str, Any]], reading: dict[str, Any],
                   snapshot_digest: str) -> dict[str, Any]:
    thread_id = reading["thread_id"]
    relevant = [
        entry for entry in entries
        if (entry["payload"].get("record_kind") in ("thread", "thread-lifecycle")
            and entry["payload"].get("thread_id") == thread_id)
        or (entry["payload"].get("record_kind") == "post"
            and entry["payload"].get("thread_id") == thread_id)
    ]
    sources = [_source_record(entry) for entry in relevant]
    revision_digest = sha256(json.dumps(
        sources, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    relations = [{"relation": "channel", "target_id": reading["channel_id"]}]
    relations.extend({
        "relation": "post",
        "target_id": post["post_id"],
        "target_address": post["content_address"],
        "target_digest": post["content_digest"],
    } for post in reading["posts"])
    addresses = {entry["entry_id"] for entry in relevant}
    return {
        "schema_version": "soveraeign-node-object-record/v1",
        "object_id": thread_id,
        "object_kind": "thread",
        "source": {
            "service_id": "console",
            "projection": "console.thread",
            "projection_authoritative": False,
            "snapshot_digest": snapshot_digest,
            "records": sources,
        },
        "revision": {
            "address": f"urn:sha256:{revision_digest}",
            "digest": revision_digest,
        },
        "relations": relations,
        "receipt_refs": _receipt_refs(entries, addresses),
        "data": reading,
    }


__all__ = ["ConsoleRoutes"]
