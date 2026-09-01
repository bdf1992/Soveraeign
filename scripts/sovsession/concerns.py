"""Open-addressed concern attribution for repository sessions.

A concern tells us what a session is serving. It is attribution and routing,
never authority. The vocabulary is deliberately open: Phase 1.5 can exercise
a small set of concerns while later citizens can mint new addresses without a
kernel enum or code change.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import os
import uuid

from sovsession import store


def _text(value: object) -> str:
    return str(value or "").strip()


def _refs(values: Iterable[str] | None, env_name: str) -> list[str]:
    """Merge explicit references with comma-separated host hints."""
    candidates = list(values or [])
    candidates.extend(item.strip() for item in os.environ.get(env_name, "").split(","))
    result: list[str] = []
    for item in candidates:
        value = _text(item)
        if value and value not in result:
            result.append(value)
    return result


def resolve(explicit: str | None, session: str) -> tuple[str, str]:
    """Resolve one concern without imposing a closed concern vocabulary."""
    if _text(explicit):
        return _text(explicit), "EXPLICIT"
    if _text(os.environ.get("SOV_CONCERN")):
        return _text(os.environ["SOV_CONCERN"]), "ENVIRONMENT"
    return "concern:session/" + session, "SESSION_FALLBACK"


def session_fields(session: str, explicit: str | None = None,
                   source_session: str | None = None,
                   sources: Iterable[str] | None = None,
                   queues: Iterable[str] | None = None) -> dict[str, Any]:
    """The concern lineage a registration event carries."""
    concern_id, binding_source = resolve(explicit, session)
    return {
        "concern": concern_id,
        "concern_binding_source": binding_source,
        "source_session": _text(source_session) or _text(os.environ.get("SOV_SOURCE_SESSION")),
        "source_refs": _refs(sources, "SOV_SOURCES"),
        "queue_refs": _refs(queues, "SOV_QUEUES"),
    }


def binding_defect(existing: dict[str, Any] | None, proposed: str) -> str | None:
    """A live session may enrich context but may not silently change concern."""
    current = _text((existing or {}).get("concern"))
    if current and proposed and current != proposed and (existing or {}).get("live"):
        return f"SESSION_CONCERN_IMMUTABLE: {current} -> {proposed}"
    return None


def record_route(directory: Path, session_record: dict[str, Any], destination: str,
                 sources: Iterable[str] | None = None, queue_ref: str = "",
                 disposition: str = "PENDING") -> dict[str, Any]:
    """Record a concern crossing without admitting work, custody, or authority."""
    source_concern = _text(session_record.get("concern"))
    destination = _text(destination)
    if not source_concern or not destination:
        raise ValueError("a concern route needs source and destination concerns")
    event = {
        "event": "concern-route",
        "route_id": "route:" + uuid.uuid4().hex,
        "session": _text(session_record.get("session")),
        "source_session": _text(session_record.get("source_session")),
        "source_concern": source_concern,
        "destination_concern": destination,
        "source_refs": _refs(sources, "SOV_SOURCES"),
        "queue_ref": _text(queue_ref),
        "disposition": _text(disposition) or "PENDING",
        "authority_effect": "NONE",
        "custody_effect": "NONE",
    }
    return store.append(directory, store.CONCERN_ROUTES_LOG, event)


def routes(directory: Path) -> list[dict[str, Any]]:
    return list(store.read(directory, store.CONCERN_ROUTES_LOG))


def enumerate_concerns(directory: Path) -> list[str]:
    """Enumerate observed addresses; an unused directory is naturally empty."""
    found: set[str] = set()
    for event in store.read(directory, store.SESSIONS_LOG):
        value = _text(event.get("concern"))
        if value:
            found.add(value)
    for event in routes(directory):
        for key in ("source_concern", "destination_concern"):
            value = _text(event.get(key))
            if value:
                found.add(value)
    return sorted(found)


def available_skills(root: Path) -> list[str]:
    """Discover skills from repository bytes rather than a hardcoded domain list."""
    directory = root / ".claude" / "skills"
    if not directory.is_dir():
        return []
    return sorted(entry.name for entry in directory.iterdir()
                  if entry.is_dir() and (entry / "SKILL.md").is_file())
