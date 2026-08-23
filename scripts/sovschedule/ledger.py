"""Append-only run ledger of kernel event envelopes, plus the single-runner lock.

Both live under ``.local/schedules/`` (gitignored runtime state; effect class
RECORD_LOCAL). Each ledger line wraps one event envelope that validates against
``contracts/event-envelope.schema.json``; the wrapper carries only the harness
index fields (schedule, run_id). Nothing here is authoritative: the ledger is a
record of attempts and reports that a later witness may observe.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json


LOCAL_DIR = Path(".local") / "schedules"
LEDGER_NAME = "ledger.ndjson"
LOCK_NAME = "lock.json"
RUNS_DIR = "runs"
TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def local_dir(root: Path) -> Path:
    return root / LOCAL_DIR


def ledger_path(root: Path) -> Path:
    return local_dir(root) / LEDGER_NAME


def runs_dir(root: Path) -> Path:
    return local_dir(root) / RUNS_DIR


def digest_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_path(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def timestamp(moment: datetime) -> str:
    """Render an aware (or naive local) datetime as a UTC ``Z`` timestamp."""
    if moment.tzinfo is None:
        moment = moment.astimezone()
    return moment.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)


def parse_timestamp(text: str) -> datetime:
    return datetime.strptime(text, TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)


def envelope(
    *,
    event_id: str,
    operation_id: str,
    phase: str,
    actor_id: str,
    actor_kind: str,
    reason: str,
    occurred_at: str,
    inputs: list[dict],
    outputs: list[dict],
    effect_class: str,
    outcome: str,
) -> dict:
    """Build a kernel event envelope; the harness holds no grants and issues no receipt."""
    return {
        "event_id": event_id,
        "operation_id": operation_id,
        "event_phase": phase,
        "actor_id": actor_id,
        "actor_kind": actor_kind,
        "reason": reason,
        "occurred_at": occurred_at,
        "inputs": list(inputs),
        "outputs": list(outputs),
        "authority_grant_ids": [],
        "effect_class": effect_class,
        "outcome": outcome,
        "receipt_id": None,
    }


def append(root: Path, schedule: str, run_id: str, event: dict) -> Path:
    """Append one wrapped event as a single JSON line."""
    path = ledger_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps({"schedule": schedule, "run_id": run_id, "event": event}, sort_keys=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
    return path


def read(root: Path, schedule: str | None = None) -> list[dict]:
    """Read ledger entries in order, optionally filtered to one schedule."""
    path = ledger_path(root)
    if not path.is_file():
        return []
    entries = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return [entry for entry in entries if schedule is None or entry["schedule"] == schedule]


def last_attempt(root: Path, schedule: str) -> datetime | None:
    """UTC time of the most recent ATTEMPTED-phase event for a schedule, refusals included."""
    attempts = [e for e in read(root, schedule) if e["event"]["event_phase"] == "ATTEMPTED"]
    if not attempts:
        return None
    return parse_timestamp(attempts[-1]["event"]["occurred_at"])


class Lock:
    """Single-runner lock: one scheduled run in the working tree at a time."""

    def __init__(self, root: Path) -> None:
        self.path = local_dir(root) / LOCK_NAME

    def holder(self) -> dict | None:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def is_held(self, now: datetime, ttl_seconds: int) -> bool:
        holder = self.holder()
        if holder is None:
            return False
        started = parse_timestamp(holder["started_at"])
        age = now.astimezone(timezone.utc) - started
        return age.total_seconds() < ttl_seconds

    def acquire(self, run_id: str, now: datetime, ttl_seconds: int) -> bool:
        if self.is_held(now, ttl_seconds):
            return False
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"run_id": run_id, "started_at": timestamp(now)}
        self.path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        return True

    def release(self) -> None:
        self.path.unlink(missing_ok=True)
