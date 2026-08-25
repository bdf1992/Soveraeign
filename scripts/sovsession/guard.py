"""Verdicts a PreToolUse hook can act on, expressed as data.

Nothing here refuses anything by itself; it returns a decision and the evidence
behind it, and the hook script turns that into an exit code. Keeping the
judgement in a plain function is what makes it testable offline, in CI, with no
sessions running at all.

Three verdicts:

  allow  nothing to say
  warn   the caller should see this and then proceed
  deny   proceeding would probably destroy another live session's work

Every deny names an escape. A guard that can wedge a repository is worse than
the collisions it prevents.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import re

from sovsession import claims, store

ALLOW, WARN, DENY = "allow", "warn", "deny"

HOT_SECONDS = 900.0
"""How recently a claim must have been touched to refuse a same-tree write.

A session holds its claims for as long as it lives, which is the right answer
for "who is working on this" and the wrong one for "may I write here". A file
someone edited two hours ago and moved on from should not be locked against the
rest of the repository, so an older claim degrades from a refusal to a report.
The lost updates this guards against all happened within minutes of each other.
"""

GIT_START = r"(?:^|[;&|\n])\s*(?:sudo\s+)?git\s+(?:-[^\s]+\s+|-C\s+\S+\s+)*"
"""A git invocation at a command boundary, not those three letters inside a string."""

BLANKET_ADD = re.compile(
    GIT_START + r"(?:add\s+(?:-A\b|--all\b|\.(?:\s|$))"
    r"|commit\s+(?:-\S*a\S*|--all)\b)")
"""The staging shapes that sweep a whole tree rather than named pathspecs."""

DESTRUCTIVE = re.compile(
    GIT_START + r"(?:reset\s+--hard\b|clean\s+-\S*[fd]|checkout\s+(?:--\s+)?\.(?:\s|$)"
    r"|restore\s+(?:--\S+\s+)*\.(?:\s|$))")
"""Commands that discard uncommitted work in the tree they run in."""

HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1.*?^\2\s*$", re.DOTALL | re.MULTILINE)
"""A heredoc body: text handed to another program, not commands this shell runs."""

QUOTED = re.compile(r"'[^']*'|\"[^\"]*\"")
"""A quoted span: data, not an invocation."""

CD_TARGET = re.compile(
    r"""(?:^|&&|;|\|\|)\s*cd\s+(?:-{1,2}\S+\s+)*("[^"]+"|'[^']+'|[^\s;&|]+)""")
"""A `cd` inside the command itself, which moves where everything after it runs."""

GIT_C_TARGET = re.compile(r"""git\s+-C\s+("[^"]+"|'[^']+'|[^\s;&|]+)""")
"""`git -C <path>`, which retargets one git command without moving the shell."""

GATE_SWALLOW = re.compile(
    r"(verify|lint)\.py[^|]*\|\s*(?:tail|head)\b[^&|]*&&")
"""A gate piped into tail before `&&`: the pipeline's status is tail's, always zero."""


def scrub(command: str) -> str:
    """Blank out the parts of a command that are data rather than invocations.

    A session writing documentation or a test about this guard puts the literal
    staging command inside a heredoc or a quoted sentence, and a bare substring
    match refuses that write. This one refused the very edit that fixed it.
    Only what the shell would actually execute counts.
    """
    return QUOTED.sub(" ", HEREDOC.sub(" ", command))


def target_directory(command: str) -> str:
    """The directory a command will actually run git in, if it names one.

    A session's working directory is not where its commands run. A session
    standing in the shared tree routinely writes `cd ../sov-budget && git add -A`,
    and judging that against the shared tree refuses a blanket stage in a
    worktree the session has entirely to itself - which is the one place the
    isolation is real and the guard should be silent.

    Returns the last such directory named, or the empty string.
    """
    found = ""
    for pattern in (CD_TARGET, GIT_C_TARGET):
        for match in pattern.finditer(command):
            found = match.group(1).strip("\"'")
    return found


def _verdict(decision: str, reason: str, **extra: Any) -> dict[str, Any]:
    """Assemble one verdict record."""
    return {"decision": decision, "reason": reason, **extra}


def guard_write(directory: Path, session: str, path: str, tree: str,
                at: datetime | None = None) -> dict[str, Any]:
    """Judge a write to one repository-relative path."""
    at = at or datetime.now(timezone.utc)
    found = claims.conflicts(directory, session, path, tree, at)
    if not found:
        return _verdict(ALLOW, "no live peer holds this path", path=path)
    same = [item for item in found if item["kind"] == claims.SAME_TREE
            and _hot(item)]
    if same:
        holder = same[0]
        return _verdict(
            DENY,
            f"{holder['session']} has held {path} in this same working tree "
            f"for {_age(holder)}. A whole-file rewrite here discards their edit.",
            path=path, conflicts=found,
            escape=f"python scripts/sov_session.py claim {path} --force "
                   f"(takes the claim, and tells them you did)")
    holder = found[0]
    if holder["kind"] == claims.SAME_TREE:
        return _verdict(
            WARN,
            f"{holder['session']} last wrote {path} in this same working tree "
            f"{_age(holder)} ago and may still have it open. Read the file before "
            f"rewriting it whole.",
            path=path, conflicts=found)
    return _verdict(
        WARN,
        f"{holder['session']} holds {path} in {holder.get('tree') or 'another tree'} "
        f"on {holder.get('branch') or 'another branch'}. Different files on disk, so "
        f"no lost update - but these two edits meet at merge.",
        path=path, conflicts=found)


def _hot(holder: dict[str, Any]) -> bool:
    """Whether a claim was touched recently enough to refuse a write over it."""
    seconds = holder.get("age_seconds")
    return seconds is None or seconds < HOT_SECONDS


def _age(holder: dict[str, Any]) -> str:
    """Render a claim's age for a human reading a refusal."""
    seconds = holder.get("age_seconds")
    if seconds is None:
        return "an unknown time"
    if seconds < 120:
        return f"{int(seconds)}s"
    return f"{int(seconds) // 60}m"


def tree_peers(directory: Path, session: str, tree: str,
               at: datetime | None = None) -> list[dict[str, Any]]:
    """Live sessions other than this one working the same checkout."""
    peers = []
    for record in store.sessions(directory, at).values():
        if not record.get("live") or record.get("session") == session:
            continue
        if record.get("tree") == tree:
            peers.append(record)
    return sorted(peers, key=lambda item: str(item.get("session", "")))


def guard_bash(directory: Path, session: str, command: str, tree: str,
               at: datetime | None = None) -> dict[str, Any]:
    """Judge a shell command about to run in this working tree."""
    at = at or datetime.now(timezone.utc)
    scrubbed = scrub(command)
    if GATE_SWALLOW.search(scrubbed):
        return _verdict(
            WARN,
            "a gate piped into tail or head before `&&` reports the pipe's exit "
            "status, not the gate's, so the `&&` fires over a red run. Run the "
            "gate on its own line, or read `python scripts/verify.py --json`.",
            command=command)
    peers = tree_peers(directory, session, tree, at)
    if not peers:
        return _verdict(ALLOW, "no live peer shares this working tree")
    names = ", ".join(str(peer.get("session")) for peer in peers)
    if BLANKET_ADD.search(scrubbed):
        return _verdict(
            DENY,
            f"a blanket stage in a tree shared with {names} sweeps their "
            f"uncommitted work into your commit. Stage explicit pathspecs instead.",
            command=command, peers=peers,
            escape="git add <path> ... , or run in your own worktree "
                   "(python scripts/sov_session.py worktree new <name>)")
    if DESTRUCTIVE.search(scrubbed):
        return _verdict(
            DENY,
            f"this discards uncommitted work in a tree shared with {names}, "
            f"including theirs.",
            command=command, peers=peers,
            escape="scope it to your own paths, or work in your own worktree")
    return _verdict(ALLOW, "no guarded pattern in this command", peers=peers)
