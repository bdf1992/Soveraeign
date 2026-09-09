"""Replace files in a container's ~/.claude without destroying what was there.

Host plumbing for `remote_session_setup.py`. `.claude/` holds no standing and
grants no authority (`AGENTS.md`, Local orchestration harness).

This module owns one hazard: every file this tool writes into `~/.claude` may
already belong to somebody else. Four rules follow, and each was a defect a
witness found before it was a rule.

Ownership is proven, never inferred. Each write records the digest of what it
wrote in `.sov-bootstrap-state.json`, and a later run calls a file its own only
when that digest still matches. Judging by shape instead — "it selects our style,
its hooks are ours" — misreads an operator file that happens to look like that,
and one draft then withheld the backup from exactly the file that needed it.

The rule covers every file, not the settings alone. A draft proved it for
`settings.json` and wrote the guarantee in the plain, while `install_styles`
overwrote an operator's own output style with no copy kept, on every session
start.

Nothing is overwritten to make room. A copy goes aside under a free name, and
bytes already held aside are not held again: without the digest check the aside
copies grow without bound, and without the free name two runs in one second
produced one name and the second clobbered the first.

Modes are carried and never widened. The temporary file is created private and
raised to the target's mode only just before the rename, so the window exposes
nothing the target did not. `Path.write_text` creates at `0666 & ~umask`, which
left the full settings content readable at `0644` while the target was `0600`.
Every write in this module goes through `write_private`, including this module's
own state file: the first draft named that call as the bug and then made it,
forty lines below the sentence naming it.

Files are compared as bytes. Reading them as text folds CRLF into LF, so a file
this tool had never seen matched one it had and was replaced with nothing kept,
and a file it could not decode had no digest at all, so its aside copies grew at
every session start.

The one file exempt from all of this is `.sov-bootstrap-state.json`, which is this
tool's own record rather than anyone else's. Keys in it that this tool did not
write are carried forward, and it is not backed up.
"""

from __future__ import annotations

from pathlib import Path
import hashlib
import json
import os
import shutil

STATE_NAME = ".sov-bootstrap-state.json"
BACKUP_SUFFIX = ".sov-bootstrap-backup"


def digest(text: str) -> str:
    """Content address of the bytes `write_private` will put on disk for this text."""
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest_of(path: Path) -> str | None:
    """Content address of a file's bytes, or None when they cannot be read.

    Bytes, not decoded text. Reading as text folds CRLF into LF and fails outright
    on anything that is not UTF-8, and both cost a file: one matched a digest it
    should not have and was replaced with nothing kept, the other had no digest and
    was copied aside again at every session start.
    """
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


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


def state_path(user: Path) -> Path:
    """Where this tool records what it wrote."""
    return user / STATE_NAME


def load_state(user: Path) -> dict:
    """Digests of the files this tool last wrote, keyed by name under ~/.claude."""
    try:
        loaded = json.loads(state_path(user).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    written = loaded.get("written") if isinstance(loaded, dict) else None
    return written if isinstance(written, dict) else {}


def save_state(user: Path, written: dict) -> None:
    """Record what this run wrote, never widening the file and never dropping a key.

    Anything else in the file is carried forward: this tool owns the `written`
    key and nothing else in there is its to discard.
    """
    path = state_path(user)
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        loaded = {}
    document = loaded if isinstance(loaded, dict) else {}
    document["written"] = written
    write_private(path, json.dumps(document, indent=2) + "\n", default_mode=0o600)


def is_own_output(user: Path, key: str, path: Path) -> bool:
    """True when the file on disk is byte-identical to what this tool last wrote."""
    recorded = load_state(user).get(key)
    return isinstance(recorded, str) and digest_of(path) == recorded


def free_name(path: Path, stem: str) -> Path:
    """A sibling path that does not exist yet, so no copy displaces another."""
    candidate = path.with_name(stem)
    index = 2
    while candidate.exists():
        candidate = path.with_name(f"{stem}.{index}")
        index += 1
    return candidate


def already_held(path: Path, stem: str, held: str) -> bool:
    """True when a copy of exactly these bytes is already beside the file."""
    for sibling in sorted(path.parent.glob(f"{stem}*")):
        if digest_of(sibling) == held:
            return True
    return False


def keep_aside(user: Path, key: str, path: Path, intact: bool = True) -> str | None:
    """Copy a file aside before it is replaced, unless this tool wrote it.

    Returns the name it was kept under, or None when there was nothing to keep:
    no file, a path that is not a regular file, bytes this tool wrote, or bytes
    already held beside it from an earlier run.
    """
    if not path.exists() or not path.is_file():
        return None
    if is_own_output(user, key, path):
        # A file this tool wrote parses by construction, so `intact` adds nothing
        # here. It still decides the name the copy is kept under, below.
        return None
    held = digest_of(path)
    stem = path.name + BACKUP_SUFFIX
    if not intact:
        stem = f"{path.name}.unparsed"
    if held is not None and already_held(path, stem, held):
        return None
    kept = free_name(path, stem)
    shutil.copyfile(path, kept)
    return kept.name


def write_private(path: Path, text: str, default_mode: int = 0o600) -> None:
    """Replace a file atomically, keeping its mode and never widening it in between.

    A symlink is written through rather than replaced, so an operator's
    indirection survives a run.
    """
    if path.is_symlink():
        path = path.resolve()
    mode = path.stat().st_mode & 0o777 if path.is_file() else default_mode
    tmp = free_name(path, f"{path.name}.tmp-{os.getpid()}")
    handle = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            tmp.unlink()


def replace_file(user: Path, key: str, path: Path, text: str, intact: bool = True) -> str | None:
    """Keep what is there, write the new bytes, and record that this tool wrote them."""
    kept = keep_aside(user, key, path, intact)
    write_private(path, text)
    written = load_state(user)
    written[key] = digest(text)
    save_state(user, written)
    return kept
