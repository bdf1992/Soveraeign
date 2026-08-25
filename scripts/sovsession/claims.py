"""Path claims: who is presently writing what, and where.

A claim is repository-relative, so `scripts/verify.py` names the same logical
file from every worktree. Two sessions holding one path is not automatically a
defect, and the distinction matters:

  same tree   both sessions write the same bytes on disk. A read-modify-write by
              either one silently discards the other's edit. This is the failure
              that actually happened, three times, on 2026-08-23.
  cross tree  different files on disk, no lost update, but the two edits will
              meet at merge. Worth saying out loud; never worth refusing.

Claims are taken automatically on the first write to a path, so the record stays
accurate without anyone remembering to declare anything.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
import re
import subprocess

from sovsession import store

SAME_TREE = "SAME_TREE"
CROSS_TREE = "CROSS_TREE"

DECISION_PATTERN = re.compile(r"^(\d{4})-")


def relative(path: str | Path, root: Path) -> str:
    """Express a path relative to its repository root, in POSIX form."""
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (root / candidate)
    try:
        resolved = candidate.resolve()
    except OSError:
        resolved = candidate
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def within_repo(path: str) -> bool:
    """Whether a path `relative` could express against the repository root.

    Both path conventions are checked because a claim travels as a string
    between worktrees: on Windows `Path("/tmp/x").is_absolute()` is False,
    since a leading slash there is drive-relative rather than absolute.

    `relative` hands back an absolute path when the target lies outside the
    repository - a scratchpad file, a temp directory, anything a session writes
    that git will never see. Those cannot collide through this repository, so
    claiming them only crowds the list with paths nobody can act on.
    """
    if path.startswith("resource:"):
        return True
    return not (PureWindowsPath(path).is_absolute() or PurePosixPath(path).is_absolute())


def claim(directory: Path, session: str, paths: list[str], tree: str,
          intent: str = "", at: str | None = None) -> list[dict[str, Any]]:
    """Record that a session is writing these repository-relative paths."""
    written = []
    for path in paths:
        record: dict[str, Any] = {
            "event": "claim", "session": session, "path": path,
            "tree": tree, "intent": intent,
        }
        if at:
            record["at"] = at
        written.append(store.append(directory, store.CLAIMS_LOG, record))
    return written


def release(directory: Path, session: str, paths: list[str],
            at: str | None = None) -> list[dict[str, Any]]:
    """Record that a session is done with these paths."""
    written = []
    for path in paths:
        record: dict[str, Any] = {"event": "release", "session": session, "path": path}
        if at:
            record["at"] = at
        written.append(store.append(directory, store.CLAIMS_LOG, record))
    return written


def held(directory: Path, at: datetime | None = None) -> dict[str, list[dict[str, Any]]]:
    """Project the claim log into live holders per path.

    A claim survives only while its session is live: a session that exits or
    falls silent releases everything it held, because the alternative is a
    repository nobody may write.
    """
    live = store.sessions(directory, at)
    current: dict[tuple[str, str], dict[str, Any]] = {}
    for event in store.read(directory, store.CLAIMS_LOG):
        session, path = event.get("session"), event.get("path")
        if not session or not path:
            continue
        key = (str(session), str(path))
        if event.get("event") == "release":
            current.pop(key, None)
        elif event.get("event") == "claim":
            current[key] = dict(event)
    by_path: dict[str, list[dict[str, Any]]] = {}
    for (session, path), record in current.items():
        if not live.get(session, {}).get("live"):
            continue
        record = dict(record)
        record["tree"] = record.get("tree") or live.get(session, {}).get("tree", "")
        record["branch"] = live.get(session, {}).get("branch", "")
        by_path.setdefault(path, []).append(record)
    return by_path


def conflicts(directory: Path, session: str, path: str, tree: str,
              at: datetime | None = None) -> list[dict[str, Any]]:
    """Every live claim on `path` by a session other than this one.

    Each result carries a `kind` of SAME_TREE or CROSS_TREE and an `age_seconds`,
    so a caller can refuse the first and merely report the second.
    """
    at = at or datetime.now(timezone.utc)
    found = []
    for record in held(directory, at).get(path, []):
        if record.get("session") == session:
            continue
        entry = dict(record)
        entry["kind"] = SAME_TREE if record.get("tree") == tree else CROSS_TREE
        try:
            entry["age_seconds"] = round(
                (at - store.parse_time(str(record.get("at")))).total_seconds())
        except (ValueError, TypeError):
            entry["age_seconds"] = None
        found.append(entry)
    return sorted(found, key=lambda item: item.get("session", ""))


def reserved_decisions(directory: Path, at: datetime | None = None) -> dict[int, str]:
    """Decision numbers presently claimed by a live session but not yet on disk."""
    taken: dict[int, str] = {}
    for path, holders in held(directory, at).items():
        if not path.startswith("decisions/"):
            continue
        match = DECISION_PATTERN.match(Path(path).name)
        if match and holders:
            taken[int(match.group(1))] = str(holders[0].get("session", ""))
    return taken


def numbers_in_history(root: Path) -> set[int]:
    """Every decision number ever added on any ref, not only on this branch.

    One `git log --all` beats one `ls-tree` per branch, and it also sees numbers
    whose file was later renamed or removed. A number that once existed is spent:
    reusing it would make two different decisions share an identifier.
    """
    result = subprocess.run(
        ["git", "log", "--all", "--diff-filter=A", "--name-only", "--format=",
         "--", "decisions/"],
        cwd=str(root), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return set()
    found = set()
    for line in result.stdout.splitlines():
        match = DECISION_PATTERN.match(Path(line.strip()).name)
        if match:
            found.add(int(match.group(1)))
    return found


def next_decision_number(root: Path, directory: Path,
                         at: datetime | None = None,
                         search_history: bool = True) -> int:
    """One past the highest number on disk, in history, or reserved by a live peer.

    Never fills a gap. A missing number means a record was retired or lives on a
    branch this tree has not seen, and handing it out again would give two
    decisions one identifier.

    Reading disk alone produced the 0039 / 0040 / 0041 collision on 2026-08-23:
    three sessions each saw the same highest number and each took the next one.
    """
    used = set(reserved_decisions(directory, at))
    decisions = root / "decisions"
    if decisions.is_dir():
        for entry in decisions.iterdir():
            match = DECISION_PATTERN.match(entry.name)
            if match:
                used.add(int(match.group(1)))
    if search_history:
        used |= numbers_in_history(root)
    return max(used) + 1 if used else 1
