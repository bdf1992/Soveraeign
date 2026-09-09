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
cannot reach a workstation. `user_settings.py` owns what happens to the file it
replaces: nothing this tool did not itself write is dropped without a copy kept
beside it. It preserves every key and every hook entry that does
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from user_settings import read_settings, replace_file  # noqa: E402

STYLE_NAME = "Communications"

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


def inside(value: object, repo: Path) -> bool:
    """True when a string names a path inside this repository, by path component."""
    if not isinstance(value, str) or not value:
        return False
    try:
        return Path(value).resolve().is_relative_to(repo)
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def ours(entry: object, repo: Path) -> bool:
    """True when a registered hook entry runs a script inside this repository.

    The root is resolved here rather than trusted from the caller: `inside()`
    resolves the entry's path, and comparing a resolved path against an
    unresolved root reports every entry as foreign under a symlinked parent.
    """
    if not isinstance(entry, dict):
        return False
    repo = repo.resolve()
    for hook in entry.get("hooks") or []:
        if not isinstance(hook, dict):
            continue
        if inside(hook.get("command"), repo):
            return True
        if any(inside(arg, repo) for arg in hook.get("args") or []):
            return True
    return False


def install_styles(repo: Path, user: Path) -> tuple[int, list[str]]:
    """Copy every output style this repository declares, keeping what it replaces.

    A style file is somebody else's until this tool has written it. An earlier
    draft copied over one without a backup, on every session start, while the
    documented guarantee said nothing was replaced without a copy kept.
    """
    source = repo / ".claude" / "output-styles"
    target = user / "output-styles"
    if not source.is_dir():
        return 0, []
    target.mkdir(parents=True, exist_ok=True)
    copied, kept = 0, []
    for style in sorted(source.glob("*.md")):
        try:
            aside = replace_file(
                user, f"output-styles/{style.name}", target / style.name,
                style.read_text(encoding="utf-8"))
        except OSError as exc:
            # One style nobody can read must not cost the session its hooks.
            print(f"sov-bootstrap: {style.name} not installed ({type(exc).__name__}).")
            continue
        if aside:
            kept.append(aside)
        copied += 1
    return copied, kept


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


def merge_hooks(existing: object, repo: Path) -> dict:
    """Replace only this repository's hook entries, preserving everyone else's.

    A `hooks` value that is not an object used to raise out of here and be
    swallowed by the top-level handler, so a session registered nothing and said
    nothing, at every start.
    """
    if not isinstance(existing, dict):
        existing = {}
    merged = {key: value for key, value in existing.items() if key not in HOOKS}
    for event in HOOKS:
        entries = existing.get(event)
        kept = [e for e in entries if not ours(e, repo)] if isinstance(entries, list) else []
        merged[event] = kept + hook_entries(repo, event)
    return merged


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
    user.mkdir(parents=True, exist_ok=True)
    settings = user / "settings.json"
    current, intact = read_settings(settings)
    styles, kept_styles = install_styles(repo, user)
    current["outputStyle"] = STYLE_NAME
    current["hooks"] = merge_hooks(current.get("hooks") or {}, repo)
    kept = replace_file(user, "settings.json", settings, json.dumps(current, indent=2) + "\n",
                        intact)

    aside = list(kept_styles)
    if not intact:
        where = f"its bytes are kept at {kept}" if kept else "nothing could be kept"
        print(f"sov-bootstrap: {settings.name} did not parse; {where}.")
    elif kept:
        aside.append(kept)
    for name in aside:
        print(f"sov-bootstrap: what was there is kept at {name}.")

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
