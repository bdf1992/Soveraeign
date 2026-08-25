"""Append-preserving storage for leases and draws, alongside the session logs.

Two logs live next to `sessions.ndjson` and `claims.ndjson` under the repository's common
git directory, so a lease is visible from every worktree without anything being committed:

  leases.ndjson  take / helper / close / release / fail, one line per event
  draws.ndjson   one line per unit of consumption or emission

Nothing here ever rewrites a line. A lease's current state is a projection over its
events, which is the same shape the session registry already uses and the same shape
`AGENTS.md` requires of the operational record: the counter-record is added, the original
stays.

The lease record this projects is the one `contracts/work-lease.schema.json` describes.
This module does not validate it - `scripts/sovkernel/work_lease.py` judges records and
the fixture harness checks shape - so that storage stays storage.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import re

from sovsession import store as session_store

LEASES_LOG = "leases.ndjson"
DRAWS_LOG = "draws.ndjson"

#: Terminal states. A lease in one of these is no longer possessed by anybody.
CLOSED_STATES = ("RELEASED", "EXPIRED", "COMPLETED", "FAILED")

_SLUG = re.compile(r"[^a-z0-9]+")


def store_dir(cwd: Path | None = None) -> Path:
    """The one store shared by every worktree, the same directory sessions use."""
    return session_store.store_dir(cwd)


def slug(text: str, fallback: str = "concern") -> str:
    """A lease-id fragment that satisfies the contract's pattern.

    The pattern is deliberately narrow: a lease id ends up in receipts and reports, and
    one that carries a path separator or a hash reads as an address rather than a name.
    """
    cleaned = _SLUG.sub("-", text.strip().lower()).strip("-")
    return cleaned or fallback


def principal_id(session: str, kind: str = "instance") -> str:
    """The instance principal for one running participant.

    Derived from the session name rather than minted separately, because the session name
    is already inherited by every subprocess a session launches. Two runs of the same
    agent definition are two sessions and therefore two principals, which is the property
    that makes attribution mean anything.
    """
    return f"urn:soveraeign:principal:{kind}:{session}"


def append(directory: Path, log: str, record: dict[str, Any]) -> dict[str, Any]:
    """Append one lease or draw event, stamped if the caller did not stamp it."""
    return session_store.append(directory, log, record)


def read(directory: Path, log: str) -> Iterable[dict[str, Any]]:
    """Yield every well-formed event in a log, skipping any torn line."""
    return session_store.read(directory, log)


def leases(directory: Path) -> dict[str, dict[str, Any]]:
    """Project the lease log into one current record per lease.

    A `take` or `helper` event carries the whole lease; later events change only the
    fields the transition owns. Replaying in order means the newest event wins without
    any line ever being edited.
    """
    projected: dict[str, dict[str, Any]] = {}
    for event in read(directory, LEASES_LOG):
        lease_id = event.get("lease_id")
        if not lease_id:
            continue
        kind = event.get("event")
        if kind in ("take", "helper"):
            record = dict(event.get("lease") or {})
            record["lease_id"] = lease_id
            projected[lease_id] = record
        elif lease_id in projected:
            record = projected[lease_id]
            if kind == "close":
                record["state"] = "COMPLETED"
                record["closure_evidence"] = event.get("closure_evidence")
            elif kind == "release":
                record["state"] = "RELEASED"
            elif kind == "fail":
                record["state"] = "FAILED"
                record["note"] = event.get("reason", "")
    return projected


def draws(directory: Path) -> list[dict[str, Any]]:
    """Every draw event, in the order it was written."""
    return list(read(directory, DRAWS_LOG))


def next_fence(existing: dict[str, dict[str, Any]], lease_id: str) -> int:
    """The fence a new holder of this lease presents: one past whatever holds it now."""
    current = existing.get(lease_id)
    return int(current.get("fence", 0)) + 1 if current else 1


def orphaned(directory: Path, live_sessions: set[str]) -> list[str]:
    """Leases still recorded as held by a session that is no longer running.

    Not a defect on its own - a session can die mid-work - but it is the difference
    between a concern somebody is holding and a concern that merely has a name on it,
    which is the whole reason this record exists.
    """
    return sorted(
        lease_id for lease_id, lease in leases(directory).items()
        if lease.get("state") not in CLOSED_STATES
        and (lease.get("holder", {}).get("session") or "") not in live_sessions
    )
