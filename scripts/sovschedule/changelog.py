"""The append-preserving record of every attempt to change a schedule declaration.

Committed, unlike the run ledger. The effective state lives in the declaration and git
carries it; if the provenance lived under ``.local/`` then cloning this repository would
produce a node whose automations are armed with no record of who armed them. A run is a
local event and its ledger is local. A switch is a decision about the repository.

Three kinds of change land here: moving the switch, creating a declaration, and editing
one. They share a record because an operator asking what happened to a schedule should
read one file rather than merging two by timestamp.

Refused attempts are appended too. A log that records only what succeeded cannot answer
the question an operator asks after an incident, which is who tried.

Nothing here is authoritative and nothing here is a receipt. It is a record of what a
binding asked for and what the operation did about it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

from sovschedule.declaration import SCHEDULES_DIR

LOG_NAME = "change-log.ndjson"

#: What kind of change was attempted. SWITCH moves the enabled flag and nothing else;
#: CREATE writes a declaration that did not exist; UPDATE edits one that did.
SWITCH = "SWITCH"
CREATE = "CREATE"
UPDATE = "UPDATE"

#: What an attempt did. PROPOSED is a real outcome, not a soft failure: the model
#: binding may ask for a schedule to be armed and the asking is recorded even though
#: the switch does not move.
EFFECTED = "EFFECTED"
PROPOSED = "PROPOSED"
REFUSED = "REFUSED"
#: The switch already held the requested state. Nothing was written and nothing was
#: appended, because two operators clicking the same button is one transition, not two.
UNCHANGED = "UNCHANGED"

ENABLE = "ENABLE"
DISABLE = "DISABLE"

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def log_path(root: Path) -> Path:
    return root / SCHEDULES_DIR / LOG_NAME


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def timestamp(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)


def parse_timestamp(text: str) -> datetime:
    return datetime.strptime(text, TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)


@dataclass(frozen=True)
class Entry:
    """One recorded attempt. ``to_enabled`` is what the declaration holds afterwards."""

    schedule: str
    change: str
    direction: str
    from_enabled: bool | None
    to_enabled: bool | None
    actor_id: str
    actor_kind: str
    binding: str
    reason: str
    occurred_at: datetime
    outcome: str
    refusal_code: str | None
    before_digest: str | None
    after_digest: str | None
    #: For UPDATE, the top-level fields whose values differ. Empty for the others.
    fields: tuple[str, ...] = ()

    @property
    def moved(self) -> bool:
        return self.outcome == EFFECTED


def record(
    *,
    schedule: str,
    direction: str,
    change: str = SWITCH,
    fields: tuple[str, ...] = (),
    from_enabled: bool | None,
    to_enabled: bool | None,
    actor_id: str,
    actor_kind: str,
    binding: str,
    reason: str,
    occurred_at: datetime,
    outcome: str,
    refusal_code: str | None = None,
    before_digest: str | None = None,
    after_digest: str | None = None,
) -> dict:
    """Build one log line. Keys are ordered so the file diffs readably."""
    return {
        "schedule": schedule,
        "change": change,
        "direction": direction,
        "fields": list(fields),
        "from_enabled": from_enabled,
        "to_enabled": to_enabled,
        "actor_id": actor_id,
        "actor_kind": actor_kind,
        "binding": binding,
        "reason": reason,
        "occurred_at": timestamp(occurred_at),
        "outcome": outcome,
        "refusal_code": refusal_code,
        "before_digest": before_digest,
        "after_digest": after_digest,
    }


def append(root: Path, entry: dict) -> None:
    """Append one line. The file is created on first use; nothing is ever rewritten."""
    path = log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def read(root: Path) -> list[Entry]:
    """Every recorded attempt, oldest first. A malformed line is skipped, not fatal.

    Skipped rather than fatal because this log is read by a health surface: a truncated
    write during a crash must not take down the page that would tell you about it.
    """
    path = log_path(root)
    if not path.is_file():
        return []
    out: list[Entry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            out.append(Entry(
                schedule=raw["schedule"],
                change=raw.get("change", SWITCH),
                direction=raw["direction"],
                from_enabled=raw.get("from_enabled"),
                to_enabled=raw.get("to_enabled"),
                actor_id=raw["actor_id"],
                actor_kind=raw["actor_kind"],
                binding=raw["binding"],
                reason=raw.get("reason", ""),
                occurred_at=parse_timestamp(raw["occurred_at"]),
                outcome=raw["outcome"],
                refusal_code=raw.get("refusal_code"),
                before_digest=raw.get("before_digest"),
                after_digest=raw.get("after_digest"),
                fields=tuple(raw.get("fields", ())),
            ))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue
    return out


def for_schedule(root: Path, name: str) -> list[Entry]:
    return [entry for entry in read(root) if entry.schedule == name]


def last_move(entries: list[Entry], name: str) -> Entry | None:
    """The newest attempt that actually changed this schedule, if any.

    Refusals and proposals are deliberately skipped here: this answers "who armed it",
    and a refused attempt did not arm anything. The refusals stay in the log and the
    surface shows them separately.
    """
    moves = [entry for entry in entries if entry.schedule == name and entry.moved]
    return moves[-1] if moves else None
