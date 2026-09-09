#!/usr/bin/env python3
"""Install this repository's operator configuration into a remote container's ~/.claude.

Host plumbing. `.claude/` holds no standing and grants no authority (`AGENTS.md`,
Local orchestration harness). This script changes nothing in the repository and
nothing outside the container it runs in.

Why it exists. A Claude Code session on the web or a phone attaches several
repositories and starts in their shared parent directory, one level above every
one of them. Project settings are discovered from the working directory
downward, so `Soveraeign/.claude/settings.json` is never read: the Communications
output style is not applied and not one session hook is registered. The same file
loads normally when a session starts inside the repository, which is why this
affects the remote hosts and no other.

What it does. Copies the output styles to `~/.claude/output-styles/`, selects
Communications, and registers the session hooks with absolute paths so they stop
depending on the working directory. User settings apply whatever the working
directory is, which is the property the project file lacks here.

What it refuses. It writes nothing unless `CLAUDE_CODE_REMOTE` is `true`, so it
cannot reach a workstation. It preserves every key and every hook entry that does
not run a script inside this repository, and it decides that by path component
rather than by substring: `/repos/Soveraeign-fork` is not inside
`/repos/Soveraeign`, and a substring test says it is. That is trap T3 in
`CLAUDE.md`, and reaching for `in` here deleted a sibling repository's hooks in
test.

Which hooks. The three `SessionStart` readings, the two `SessionEnd` closers, the
per-turn prose reminder, and itself: seven entries. It leaves out the
`PreToolUse` and `PostToolUse` path-claim hooks. Those exist to stop two live
sessions clobbering one shared working tree and to record what each one holds; a
remote container has its own clone, so registering them protects against nothing
here and the `PreToolUse` pair can refuse a legitimate write.

Why it registers itself. Not to survive a missing clone: the entry point lives
inside the clone, so a setup script that runs before cloning never reaches this
file at all. It registers itself so that `~/.claude` follows the repository
across the environment cache, which is reused for about seven days without
re-running the setup script.

It must never break a session. Any failure prints a short note and exits 0.
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import sys
import time

STYLE_NAME = "Communications"
BACKUP_SUFFIX = ".sov-bootstrap-backup"

# event -> (hook script path under .claude/, mode, timeout seconds, status message)
HOOKS: dict[str, list[tuple[str, str, int, str]]] = {
    "SessionStart": [
        ("bootstrap/remote_session_setup.py", "start", 15, "Refreshing the remote setup"),
        ("console_session.py", "start", 25, "Reading console continuity"),
        ("session_registry.py", "start", 20, "Reading the live-session registry"),
        ("stranded_work.py", "start", 20, "Checking for work left where nothing will find it"),
    ],
    "SessionEnd": [
        ("console_session.py", "end", 25, "Closing the console session"),
        ("session_registry.py", "end", 20, "Releasing session claims"),
    ],
    "UserPromptSubmit": [
        ("unslop_reminder.py", "turn", 10, "Loading the prose rules"),
    ],
}


def is_remote() -> bool:
    """True when the host declares this a remote (web or mobile) container."""
    return os.environ.get("CLAUDE_CODE_REMOTE", "").strip().lower() == "true"


def read_settings(path: Path) -> tuple[dict, bool]:
    """Read a settings object.

    Returns the object and whether the file on disk was intact. A missing file is
    intact and empty. A file that does not parse, or parses to something other
    than an object, is not: its keys cannot be preserved, so the caller keeps the
    bytes aside rather than discarding them silently.
    """
    if not path.exists():
        return {}, True
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, False
    return (loaded, True) if isinstance(loaded, dict) else ({}, False)


def inside(value: object, repo: Path) -> bool:
    """True when a string names a path inside this repository, by path component."""
    if not isinstance(value, str) or not value:
        return False
    try:
        return Path(value).resolve().is_relative_to(repo)
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def ours(entry: object, repo: Path) -> bool:
    """True when a registered hook entry runs a script inside this repository."""
    if not isinstance(entry, dict):
        return False
    for hook in entry.get("hooks") or []:
        if not isinstance(hook, dict):
            continue
        if inside(hook.get("command"), repo):
            return True
        if any(inside(arg, repo) for arg in hook.get("args") or []):
            return True
    return False


def install_styles(repo: Path, target: Path) -> int:
    """Copy every output style this repository declares into the user directory."""
    source = repo / ".claude" / "output-styles"
    if not source.is_dir():
        return 0
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for style in sorted(source.glob("*.md")):
        shutil.copyfile(style, target / style.name)
        copied += 1
    return copied


def hook_entries(repo: Path, event: str) -> list[dict]:
    """Build this repository's hook entries for one event, with absolute paths."""
    entries = []
    for name, mode, timeout, message in HOOKS.get(event, []):
        script = repo / ".claude" / (name if "/" in name else f"hooks/{name}")
        if not script.is_file():
            continue
        entries.append(
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": sys.executable,
                        "args": [str(script), mode],
                        "timeout": timeout,
                        "statusMessage": message,
                    }
                ]
            }
        )
    return entries


def merge_hooks(existing: dict, repo: Path) -> dict:
    """Replace only this repository's hook entries, preserving everyone else's."""
    merged = {key: value for key, value in existing.items() if key not in HOOKS}
    for event in HOOKS:
        kept = [e for e in existing.get(event) or [] if not ours(e, repo)]
        merged[event] = kept + hook_entries(repo, event)
    return merged


def is_own_output(settings: dict, repo: Path) -> bool:
    """True when a settings object looks like one this script wrote and nobody edited."""
    if settings.get("outputStyle") != STYLE_NAME:
        return False
    hooks = settings.get("hooks")
    if not isinstance(hooks, dict) or not hooks:
        return False
    if set(hooks) - set(HOOKS):
        return False
    entries = [e for event in hooks.values() for e in event or []]
    return bool(entries) and all(ours(e, repo) for e in entries)


def preserve(settings_path: Path, existing: dict, intact: bool, repo: Path) -> str | None:
    """Keep the current file aside before it is replaced, and say where it went.

    A file that did not parse is always kept, under a stamped name, because its
    keys cannot be merged forward. An intact file is backed up once, and never
    when it is this script's own previous output: a backup of that would look
    like the state before the tool ran and would not be it.
    """
    if not settings_path.is_file():
        return None
    if not intact:
        stamp = time.strftime("%Y%m%dT%H%M%S")
        kept = settings_path.with_name(f"{settings_path.name}.unparsed-{stamp}")
        shutil.copyfile(settings_path, kept)
        return kept.name
    backup = settings_path.with_name(settings_path.name + BACKUP_SUFFIX)
    if backup.exists() or is_own_output(existing, repo):
        return None
    shutil.copyfile(settings_path, backup)
    return backup.name


def write_atomic(path: Path, text: str) -> None:
    """Write a file through a temporary sibling so an interrupted run cannot truncate it."""
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    try:
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def resolve_repo(argument: str | None) -> Path | None:
    """Resolve the repository root, ignoring an argument that is not one.

    Registered as a hook, this script is called as `python <script> <mode>`, so
    argv[1] is a mode word and not a path. Its own location is the reliable
    answer; an argument is honoured only when it names a directory that holds a
    `.claude`.
    """
    if argument:
        candidate = Path(argument).resolve()
        if (candidate / ".claude").is_dir():
            return candidate
    here = Path(__file__).resolve().parents[2]
    return here if (here / ".claude").is_dir() else None


def main() -> int:
    """Install styles and hooks, or explain why nothing was installed."""
    if not is_remote():
        print("sov-bootstrap: not a remote session, nothing written.")
        return 0

    repo = resolve_repo(sys.argv[1] if len(sys.argv) > 1 else None)
    if repo is None:
        print("sov-bootstrap: could not resolve the repository root, nothing written.")
        return 0

    user = Path.home() / ".claude"
    settings = user / "settings.json"
    current, intact = read_settings(settings)
    kept = preserve(settings, current, intact, repo)
    if not intact:
        print(f"sov-bootstrap: {settings.name} did not parse; its bytes are kept at {kept}.")

    styles = install_styles(repo, user / "output-styles")

    current["outputStyle"] = STYLE_NAME
    current["hooks"] = merge_hooks(current.get("hooks") or {}, repo)

    user.mkdir(parents=True, exist_ok=True)
    write_atomic(settings, json.dumps(current, indent=2) + "\n")

    total = sum(len(hook_entries(repo, event)) for event in HOOKS)
    events = ", ".join(f"{k} x{len(hook_entries(repo, k))}" for k in HOOKS)
    print(f"sov-bootstrap: style {STYLE_NAME} selected, {styles} style file(s) copied.")
    print(f"sov-bootstrap: {total} hook entries registered from {repo} ({events}).")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:  # never break a starting session
        print(f"sov-bootstrap: skipped ({type(exc).__name__}: {exc}).")
        code = 0
    sys.exit(code)
