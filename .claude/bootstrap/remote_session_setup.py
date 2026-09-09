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
cannot reach a workstation. It backs up an existing `~/.claude/settings.json`
once before its first write, and it preserves every key and every foreign hook
entry it does not own.

Which hooks. The three that only read and report: the console continuity
briefing, the live-session registry's own registration, and the stranded-work
reading, plus the per-turn prose reminder. The `PreToolUse` path-claim hooks are
deliberately left out. They exist to stop two live sessions clobbering one shared
working tree; a remote container holds its own clone, so registering them here
would buy no protection and could refuse a legitimate write.

It also registers itself, first. A setup script may run before the repository is
cloned and the published documentation does not say which way round. If it runs
first, this script finds no styles to copy and writes only the hook registration,
whose paths resolve when the hooks fire rather than when they are written. The
`SessionStart` entry then re-runs it with the clone present, which installs the
styles. An output style is read when a session starts, so on that path it applies
from the next session rather than the first.

It must never break a session. Any failure prints a short note and exits 0.
"""

from __future__ import annotations

from pathlib import Path
import json
import os
import shutil
import sys

STYLE_NAME = "Communications"
BACKUP_SUFFIX = ".sov-bootstrap-backup"

# event -> (hook script name, mode, timeout seconds, status message)
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


def load_json(path: Path) -> dict:
    """Read a JSON object, returning an empty one for a missing or unreadable file."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


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


def foreign(entry: object, repo: Path) -> bool:
    """True when a registered hook entry belongs to someone other than this repository."""
    return str(repo) not in json.dumps(entry)


def merge_hooks(existing: dict, repo: Path) -> dict:
    """Replace only this repository's hook entries, preserving anyone else's."""
    merged = {key: value for key, value in existing.items() if key not in HOOKS}
    for event in HOOKS:
        kept = [e for e in existing.get(event, []) if foreign(e, repo)]
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
    settings = user / "settings.json"
    backup = settings.with_name(settings.name + BACKUP_SUFFIX)
    if settings.is_file() and not backup.exists():
        shutil.copyfile(settings, backup)

    styles = install_styles(repo, user / "output-styles")

    current = load_json(settings)
    current["outputStyle"] = STYLE_NAME
    current["hooks"] = merge_hooks(current.get("hooks", {}), repo)

    user.mkdir(parents=True, exist_ok=True)
    settings.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8", newline="\n")

    events = ", ".join(f"{k} x{len(hook_entries(repo, k))}" for k in HOOKS)
    print(f"sov-bootstrap: style {STYLE_NAME} selected, {styles} style file(s) copied.")
    print(f"sov-bootstrap: hooks registered from {repo} ({events}).")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:  # never break a starting session
        print(f"sov-bootstrap: skipped ({type(exc).__name__}: {exc}).")
        code = 0
    sys.exit(code)
