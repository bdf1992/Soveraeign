"""The append-preserving store behind session registration and path claims.

State lives under the repository's *common* git directory, so every worktree of
the same repository reads and writes one store without anything being committed.
`git rev-parse --git-common-dir` resolves to the same absolute path from the
shared tree and from a worktree in a temp directory, which is what makes a claim
visible across the nineteen trees this repository currently has checked out.

Two logs:

  sessions.ndjson  register / heartbeat / end, one line per event
  claims.ndjson    claim / release, one line per event

Liveness is deliberately not a lock. A session that dies without releasing must
not wedge the repository, so a claim expires on heartbeat age, and a process
that is demonstrably alive keeps its claim past that age.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator
import json
import os
import subprocess

STALE_SECONDS = 1800.0
"""A claim whose session has not been heard from in this long is advisory only."""

SESSIONS_LOG = "sessions.ndjson"
CLAIMS_LOG = "claims.ndjson"


class StoreError(RuntimeError):
    """The store could not be located or read."""


def _git(args: list[str], cwd: Path | None = None) -> str:
    """Run a read-only git command and return its stripped stdout."""
    result = subprocess.run(
        ["git", *args], cwd=str(cwd) if cwd else None,
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise StoreError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def repo_root(cwd: Path | None = None) -> Path:
    """The top of the working tree this call is made from."""
    return Path(_git(["rev-parse", "--path-format=absolute", "--show-toplevel"], cwd))


def store_dir(cwd: Path | None = None) -> Path:
    """The one store shared by every worktree of this repository."""
    common = Path(_git(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd))
    return common / "sov-sessions"


def now() -> str:
    """An RFC 3339 UTC timestamp; injected by tests through `append`'s `at`."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    """Read a timestamp this module wrote, tolerating a trailing Z."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def append(directory: Path, log: str, record: dict[str, Any]) -> dict[str, Any]:
    """Append one event, stamping it if the caller did not.

    Opening in append mode and writing one complete line is atomic enough for
    concurrent local writers: the failure this store exists to prevent is a lost
    update to a source file, not a lost line in its own journal.
    """
    record = dict(record)
    record.setdefault("at", now())
    directory.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True, ensure_ascii=False)
    with (directory / log).open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(line + "\n")
    return record


def read(directory: Path, log: str) -> Iterator[dict[str, Any]]:
    """Yield every well-formed event in a log, skipping any torn line."""
    path = directory / log
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(record, dict):
            yield record


STILL_ACTIVE = 259
"""The Windows exit code reported for a process that has not exited."""

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
"""The narrowest access right that still permits asking whether a process lives."""


def _windows_pid_alive(pid: int) -> bool:
    """Ask Windows whether a process lives, without touching it.

    `os.kill(pid, 0)` must never be used here. CPython's Windows implementation
    opens the process with PROCESS_ALL_ACCESS and then calls TerminateProcess
    with the signal number as the exit code - so the POSIX idiom for "does this
    process exist" would terminate the process it was asked about. It only
    failed safe in this repository because opening the parent was denied.

    A process that genuinely exited with code 259 reads as alive. That is the
    documented ambiguity of GetExitCodeProcess, and erring toward alive costs a
    stale claim rather than a lost update.
    """
    import ctypes

    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        if kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
            return code.value == STILL_ACTIVE
        return True
    finally:
        kernel32.CloseHandle(handle)


def pid_alive(pid: int | None) -> bool:
    """Whether a process id still exists, by a route that cannot disturb it."""
    if not pid:
        return False
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if os.name == "nt":
        try:
            return _windows_pid_alive(pid)
        except (AttributeError, OSError):
            return False
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def sessions(directory: Path, at: datetime | None = None) -> dict[str, dict[str, Any]]:
    """Project the session log into one record per session, newest fields winning."""
    at = at or datetime.now(timezone.utc)
    projected: dict[str, dict[str, Any]] = {}
    for event in read(directory, SESSIONS_LOG):
        name = event.get("session")
        if not name:
            continue
        current = projected.setdefault(name, {"session": name})
        kind = event.get("event")
        if kind == "register":
            current.update({k: v for k, v in event.items() if k != "event"})
            current["ended"] = False
            current["registered"] = True
        elif kind == "heartbeat":
            current["at"] = event.get("at", current.get("at"))
        elif kind == "end":
            current["ended"] = True
            current["ended_at"] = event.get("at")
    for record in projected.values():
        record["live"] = is_live(record, at)
    return projected


def is_live(record: dict[str, Any], at: datetime | None = None) -> bool:
    """A session is live until it says otherwise, or falls silent and dies.

    A session that never registered is not live no matter what else it wrote. A
    claim or a heartbeat alone would otherwise conjure a session with no tree and
    no branch, which then holds paths nobody can attribute.
    """
    if record.get("ended") or not record.get("registered"):
        return False
    if pid_alive(record.get("pid")):
        return True
    stamp = record.get("at")
    if not stamp:
        return False
    at = at or datetime.now(timezone.utc)
    try:
        age = (at - parse_time(str(stamp))).total_seconds()
    except ValueError:
        return False
    return age < STALE_SECONDS
