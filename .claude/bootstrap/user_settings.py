"""Read, preserve and replace a container's ~/.claude/settings.json.

Host plumbing for `remote_session_setup.py`. `.claude/` holds no standing and
grants no authority (`AGENTS.md`, Local orchestration harness).

This module owns one hazard: the file belongs to whoever else writes it, and this
tool replaces it. Three rules follow, each of them a defect that was found in
test before it was a rule.

Ownership is proven, not inferred. After each write the digest of what was
written is recorded beside the file. A later run calls the file its own only when
the digest still matches. Judging ownership from the file's shape instead —
"it selects our style and its hooks are ours" — misreads an operator file that
happens to look like that, and the first draft then withheld the backup from
exactly the file that needed it.

Nothing is ever overwritten to make room. A file that is not ours is copied aside
before it is replaced, under the plain backup name the first time and a stamped
name after that, and a name already taken is never reused. Two runs in the same
second produced the same stamp and the second copy clobbered the first.

The replacement is atomic and keeps the file's mode. `os.replace` from a fresh
temporary file otherwise widens `0600` to `0644`, and a settings file can hold
environment values and permission rules.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import shutil
import time

STATE_NAME = ".sov-bootstrap-state.json"
BACKUP_SUFFIX = ".sov-bootstrap-backup"


def digest(text: str) -> str:
    """Content address of a settings file, as written."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_settings(path: Path) -> tuple[dict, bool]:
    """Read a settings object, and say whether the file on disk was intact.

    A missing file is intact and empty. A file that does not parse, or parses to
    something that is not an object, is not intact: its keys cannot be carried
    forward, so the caller keeps the bytes rather than dropping them.
    """
    if not path.exists():
        return {}, True
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, False
    return (loaded, True) if isinstance(loaded, dict) else ({}, False)


def recorded_digest(path: Path) -> str | None:
    """The digest this tool recorded when it last wrote that settings file."""
    state = path.with_name(STATE_NAME)
    try:
        loaded = json.loads(state.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    value = loaded.get("settings_digest") if isinstance(loaded, dict) else None
    return value if isinstance(value, str) else None


def is_own_output(path: Path) -> bool:
    """True when the file on disk is byte-identical to what this tool last wrote."""
    recorded = recorded_digest(path)
    if recorded is None:
        return False
    try:
        return digest(path.read_text(encoding="utf-8")) == recorded
    except OSError:
        return False


def free_name(path: Path, stem: str) -> Path:
    """A sibling path that does not exist yet, so no aside copy displaces another."""
    candidate = path.with_name(stem)
    index = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem}.{index}")
        index += 1
    return candidate


def preserve(path: Path, intact: bool) -> str | None:
    """Copy the current settings file aside unless this tool wrote it.

    Returns the name it was kept under, or None when there was nothing to keep.
    A file that is not a regular file is reported as unkeepable rather than
    described as saved.
    """
    if not path.exists():
        return None
    if not path.is_file():
        return None
    if intact and is_own_output(path):
        return None
    if intact:
        stem = path.name + BACKUP_SUFFIX
    else:
        stem = f"{path.name}.unparsed-{time.strftime('%Y%m%dT%H%M%S')}"
    kept = free_name(path, stem)
    shutil.copyfile(path, kept)
    return kept.name


def write_settings(path: Path, settings: dict) -> None:
    """Replace the settings file atomically, keeping its mode, and record the digest.

    The temporary sibling is created private and its mode set to the target's only
    after the bytes are down, so the window never exposes more than the original.
    """
    text = json.dumps(settings, indent=2) + "\n"
    mode = path.stat().st_mode & 0o777 if path.is_file() else 0o600
    tmp = free_name(path, f"{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()
    state = path.with_name(STATE_NAME)
    state.write_text(
        json.dumps({"settings_digest": digest(text)}, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
