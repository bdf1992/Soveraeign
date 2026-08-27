#!/usr/bin/env python3
"""Bind a Claude Code session to the live-session registry.

Host plumbing. `.claude/` holds no standing and grants no authority
(`AGENTS.md`, Local orchestration harness); every judgement here is made by
`scripts/sov_session.py`, which is testable offline and covered by
`scripts/verify.py`. This file only carries hook payloads to it and turns
verdicts into the hook protocol.

Five modes, one per hook event:

  start       SessionStart. Registers this session and prints who else is here.
              A message reaches only sessions that already exist; a briefing at
              start is the only channel that reaches one that does not yet.
  end         SessionEnd. Closes the session, releasing every claim it holds.
  pre-write   PreToolUse on Edit/Write. Refuses a write to a path another live
              session holds in this same working tree, which is the lost-update
              that cost this repository three clobbers on 2026-08-23.
  post-write  PostToolUse on Edit/Write. Claims what was just written, so the
              registry stays accurate without anyone declaring anything.
  pre-bash    PreToolUse on Bash. Refuses a blanket stage or a destructive reset
              in a tree shared with another live session.

It must never break a session. Any failure prints nothing and exits 0: a
registry that cannot be reached is a missing convenience, not a reason to refuse
to work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

HEARTBEAT_SECONDS = 120.0
WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}


def _payload() -> dict[str, Any]:
    """Read the hook payload from stdin, tolerating an empty or torn one."""
    try:
        raw = sys.stdin.read()
    except (OSError, ValueError):
        return {}
    if not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _decide(event: str, decision: str, reason: str) -> None:
    """Emit a PreToolUse verdict in the hook protocol and exit successfully."""
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": event,
        "permissionDecision": decision,
        "permissionDecisionReason": reason,
    }}))
    raise SystemExit(0)


def _context(payload: dict[str, Any], near: str = ""):
    """Load the session modules and resolve this session's identity and tree.

    `near` is the file about to be written. The tree is resolved from it rather
    than from the session's cwd, because a session standing in the shared tree
    routinely writes into one of its own worktrees, and a claim filed against
    the wrong root records an absolute path nobody else can match.
    """
    from sovsession import claims, guard, store
    import sov_session

    cwd = payload.get("cwd") or os.getcwd()
    anchor = Path(cwd)
    if near:
        candidate = Path(near)
        candidate = candidate if candidate.is_dir() else candidate.parent
        if candidate.is_dir():
            anchor = candidate
    try:
        root = store.repo_root(anchor)
    except Exception:  # noqa: BLE001 - fall back to the session's own tree
        root = store.repo_root(Path(cwd))
    payload_id = str(payload.get("session_id") or "")
    name = sov_session.session_name(
        fallback="session-" + payload_id[:6] if payload_id else None)
    return {
        "claims": claims, "guard": guard, "store": store,
        "root": root, "directory": store.store_dir(root),
        "session": name, "tree": str(root).replace("\\", "/"),
    }


def _target(payload: dict[str, Any]) -> str:
    """The file path a write tool is about to touch."""
    tool_input = payload.get("tool_input") or {}
    for key in ("file_path", "notebook_path", "path"):
        value = tool_input.get(key)
        if value:
            return str(value)
    return ""


def _ensure_registered(context: dict[str, Any]) -> None:
    """Register a session that never saw SessionStart.

    SessionStart fires only for sessions that begin after the hook is installed.
    Every session already running when it lands gets the write hooks and none of
    the registration, so it heartbeats and takes claims that the projection then
    discards, because a record with no registration is not a live session. That
    left six sessions writing this repository and nothing able to name any of
    them. Registering on first contact closes it without waiting for a restart.
    """
    store = context["store"]
    record = store.sessions(context["directory"]).get(context["session"])
    if record and record.get("registered"):
        return
    from sovsession import brief as briefmod
    store.append(context["directory"], store.SESSIONS_LOG, {
        "event": "register", "session": context["session"],
        "pid": int(os.environ.get("CLAUDE_PID", 0) or 0),
        "tree": context["tree"], "branch": briefmod.branch_of(context["root"]),
        "intent": "registered on first write, not at session start",
    })


def _beat(context: dict[str, Any]) -> None:
    """Refresh liveness, but only every couple of minutes."""
    from datetime import datetime, timezone
    store = context["store"]
    record = store.sessions(context["directory"]).get(context["session"])
    if record and record.get("at"):
        try:
            age = (datetime.now(timezone.utc) - store.parse_time(str(record["at"])))
            if age.total_seconds() < HEARTBEAT_SECONDS:
                return
        except ValueError:
            pass
    store.append(context["directory"], store.SESSIONS_LOG,
                 {"event": "heartbeat", "session": context["session"]})


def mode_start(payload: dict[str, Any]) -> None:
    """Register this session and print the briefing as its opening context."""
    context = _context(payload)
    store = context["store"]
    from sovsession import brief as briefmod
    store.append(context["directory"], store.SESSIONS_LOG, {
        "event": "register", "session": context["session"],
        "pid": int(os.environ.get("CLAUDE_PID", 0) or 0),
        "tree": context["tree"], "branch": briefmod.branch_of(context["root"]),
        "intent": "",
    })
    print(briefmod.render(briefmod.collect(
        context["root"], context["directory"], context["session"], context["tree"])))


def mode_end(payload: dict[str, Any]) -> None:
    """Close this session so its claims stop blocking anyone."""
    context = _context(payload)
    store = context["store"]
    store.append(context["directory"], store.SESSIONS_LOG,
                 {"event": "end", "session": context["session"]})


def mode_pre_write(payload: dict[str, Any]) -> None:
    """Refuse a write that would silently discard another live session's edit."""
    target = _target(payload)
    if not target:
        return
    context = _context(payload, near=target)
    path = context["claims"].relative(target, context["root"])
    if not context["claims"].within_repo(path):
        return
    verdict = context["guard"].guard_write(
        context["directory"], context["session"], path, context["tree"])
    if verdict["decision"] == context["guard"].DENY:
        _decide("PreToolUse", "deny",
                verdict["reason"] + "\nTo take it anyway: " + verdict["escape"])
    if verdict["decision"] == context["guard"].WARN:
        _decide("PreToolUse", "allow", verdict["reason"])


def mode_post_write(payload: dict[str, Any]) -> None:
    """Claim what was just written, and refresh this session's liveness."""
    target = _target(payload)
    if not target:
        return
    context = _context(payload, near=target)
    _ensure_registered(context)
    path = context["claims"].relative(target, context["root"])
    if not context["claims"].within_repo(path):
        _beat(context)
        return
    held = context["claims"].held(context["directory"]).get(path, [])
    if not any(holder.get("session") == context["session"] for holder in held):
        context["claims"].claim(context["directory"], context["session"], [path],
                                context["tree"], "auto: wrote this path")
    _beat(context)


def mode_pre_bash(payload: dict[str, Any]) -> None:
    """Refuse a command that would sweep or discard a tree-mate's uncommitted work."""
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command:
        return
    from sovsession import guard as guardmod
    elsewhere = guardmod.target_directory(command)
    context = _context(payload, near=elsewhere)
    _ensure_registered(context)
    verdict = context["guard"].guard_bash(
        context["directory"], context["session"], command, context["tree"])
    if verdict["decision"] == context["guard"].DENY:
        _decide("PreToolUse", "deny",
                verdict["reason"] + "\nInstead: " + verdict["escape"])
    if verdict["decision"] == context["guard"].WARN:
        _decide("PreToolUse", "allow", verdict["reason"])


MODES = {
    "start": mode_start,
    "end": mode_end,
    "pre-write": mode_pre_write,
    "post-write": mode_post_write,
    "pre-bash": mode_pre_bash,
}


def main(argv: list[str]) -> int:
    """Dispatch one hook mode, swallowing every failure."""
    if len(argv) < 2 or argv[1] not in MODES:
        return 0
    try:
        MODES[argv[1]](_payload())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001 - a hook must never break a session
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
