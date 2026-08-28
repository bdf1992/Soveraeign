#!/usr/bin/env python3
"""Bind a Claude Code session to a Console Service operator session.

This is host plumbing. `.claude/` holds no standing and grants no authority
(`AGENTS.md`, Local orchestration harness); everything consequential this script
does, it does by calling the Console Service through its declared machine path,
the same path any other binding uses. It writes no console state itself.

Two hook events drive it:

  start  a SessionStart hook. Opens (or resumes) this operator's console session
         and prints what landed while they were away. Whatever it prints becomes
         context for the session that is starting - that is the automatic
         metadata half of this.
  end    a SessionEnd hook. Closes the console session, which pins the read
         position the next session reads forward from. Without this the cursor
         never advances and every post reads as unseen forever.

It must never break a session. Any failure prints a short note and exits 0: a
console that cannot be reached is a missing convenience, not a reason to refuse
to start work.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STORE = ROOT / ".local" / "console"
BINDINGS = STORE / "host-sessions.json"
OPERATOR = os.environ.get("SOVERAEIGN_OPERATOR", "sov")
BINDING_ID = "claude-code"
TIMEOUT_SECONDS = 20

# A warning printed as the process exits lands after the line that names the fault.
# Reporting it as the cause sends the session after the wrong thing. Python writes
# a warning as `source:lineno: SomeWarning: text`, so the class name is matched in
# that position rather than anywhere in the line.
_WARNING = re.compile(r":\s\w*Warning:")


class ConsoleRefused(RuntimeError):
    """The console refused the call and said why in a stable code.

    The CLI writes a refusal as JSON on stdout and exits non-zero. Reading stdout
    alone cannot tell a refusal from a result, so the reason code never reached the
    session and the refusal surfaced as whichever key the caller looked up next.
    The code is what a reader can act on, so it is what this carries.
    """

    def __init__(self, command: str, stdout: str, code: int, stderr: str) -> None:
        try:
            payload = json.loads(stdout)
        except ValueError:
            payload = {}
        self.command = command
        self.reason_code = payload.get("reason_code") or "REFUSED"
        detail = stderr or payload.get("outcome") or ""
        super().__init__(
            f"console {command} refused: {self.reason_code}"
            + (f" ({detail})" if detail else ""))


def _console(*args: str) -> dict[str, Any]:
    """Call the Console Service CLI and return its JSON result."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([
        str(ROOT / "services" / "console" / "src"),
        str(ROOT / "services" / "record" / "src"),
        env.get("PYTHONPATH", ""),
    ]).rstrip(os.pathsep)
    result = subprocess.run(
        [sys.executable, "-m", "soveraeign_console_service.cli", "--root", str(STORE), *args],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    if result.returncode != 0:
        raise ConsoleRefused(args[0], result.stdout, result.returncode,
                             result.stderr.strip())
    if not result.stdout.strip():
        raise RuntimeError(result.stderr.strip() or "the console returned nothing")
    return json.loads(result.stdout)


#: What this binding spends, per contracts/capability-offices.json. Bdo ruled on
#: 2026-08-25 that the session lifecycle and the session read check the authority
#: they declare, so the operator's own store records the operator's own grants
#: before the hook uses them. Recording a grant on your own node is not the hook
#: acquiring authority; issuing there costs `grant:authority`, and if this operator
#: does not hold it the calls below refuse and the session is briefed without them.
NEEDED = ("open:session", "close:session", "read:session")


def _ensure_grants() -> None:
    """Record the operator's own session grants if they are not live yet."""
    try:
        live = _console("grants", "--reader", OPERATOR,
                        "--operator", OPERATOR)["live_grants"]
        held = {record["capability"] for record in live}
    except Exception:  # a store with no permits office read for this operator yet
        held = set()
    for capability in NEEDED:
        if capability not in held:
            _console("grant", "--operator", OPERATOR, "--capability", capability,
                     "--scope", OPERATOR, "--granted-by", OPERATOR)


def _bindings() -> dict[str, str]:
    """Map Claude Code session ids to console session ids.

    This is a host convenience, not a record. Losing it costs a resumed session
    its continuity for one turn; it cannot lose or alter anything in the journal.
    """
    try:
        return json.loads(BINDINGS.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def _remember(host_session: str, console_session: str) -> None:
    BINDINGS.parent.mkdir(parents=True, exist_ok=True)
    BINDINGS.write_text(json.dumps({**_bindings(), host_session: console_session},
                                   indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render(context: dict[str, Any], console_session: str,
            notes: list[str] | None = None) -> str:
    """Write the continuity briefing that becomes the starting session's context."""
    lines = [
        "# Console continuity",
        "",
        f"Operator `{OPERATOR}` through binding `{BINDING_ID}`. "
        f"Console session `{console_session}`.",
        "",
        "This is a rebuilt projection over the Record Service journal. It is not "
        "authoritative and settles nothing.",
        "",
    ]
    unseen = context["unseen_posts"]
    if unseen:
        lines.append(f"## Landed since this operator last closed a session ({len(unseen)})")
        lines.append("")
        for post in unseen:
            mention = " (mentions you)" if post["mentions_you"] else ""
            lines.append(f"- `{post['thread_id']}` - {post['actor_id']} "
                         f"({post['actor_kind']}) at {post['posted_at']}{mention}: "
                         f"`{post['content_address']}`")
        lines.append("")
    else:
        lines.append("Nothing landed since this operator last closed a session.\n")

    if context["open_threads"]:
        lines.append("## Open threads")
        lines.append("")
        for thread in context["open_threads"]:
            pin = f", pinned to {thread['pinned_address']}" if thread["pinned_address"] else ""
            lines.append(f"- `{thread['thread_id']}` {thread['title']} "
                         f"({thread['post_count']} posts{pin})")
        lines.append("")

    for omission in context["omissions"]:
        lines.append(f"Omission - {omission['source']}: {omission['reason']}")
    lines.append("")
    lines.append("Read a thread or post into one with the `sov-continuity` skill. "
                 "A post that makes a claim needs a proposal id; the console refuses it "
                 "otherwise.")
    if notes:
        lines.extend(["", *notes])
    return "\n".join(lines)


def _terse(failure: Exception) -> str:
    """The line naming the fault: not the traceback, and not a trailing warning.

    Whatever this hook prints becomes context for the session that is starting.
    A pasted traceback spends that context on frames the session cannot act on and
    buries the one line that names the fault (`AGENTS.md`, Context hygiene). The
    fault is usually the last line, but a warning emitted as the process exits
    lands after it and would be reported as the cause. Warnings are skipped. A
    failure that is nothing but warnings falls back to its last line rather than
    inventing a cause it cannot see.
    """
    lines = [line.strip() for line in str(failure).strip().splitlines() if line.strip()]
    if not lines:
        return type(failure).__name__
    for line in reversed(lines):
        if _WARNING.search(line) or line.startswith(("Traceback", "File ")):
            continue
        return line
    return lines[-1]


def _provenance(opened: bool) -> str:
    """What is actually known about where this console session id came from.

    An id this hook just opened is backed by a call the console answered, so that
    record committed. An id read from the binding map is backed by the map, which
    `_bindings` calls a host convenience and not a record: it outlives the session
    it names, because `end` never removes an entry, and it outlives a store that
    was replaced underneath it. Calling that "resumed" asserts the console still
    holds the session and that it is open, and this hook has checked neither. That
    is the same unbacked claim the hook exists to stop making.
    """
    if opened:
        return "opened by this hook, so the console committed that record"
    return ("carried from this host binding map, which is a convenience and not a "
            "record; whether the console still holds it, and whether it is open, "
            "is unchecked here")


def _degraded(console_session: str, opened: bool, failure: Exception,
              notes: list[str] | None = None) -> str:
    """Report a briefing this hook could not build, without misreporting the record.

    The session is opened and bound before the briefing is asked for, so a briefing
    that fails does not mean nothing was recorded. Saying so anyway is a false claim
    about the journal, which is the one thing host plumbing must never make. Report
    what is known, name what is not, and leave the diagnosis to the owning service.
    """
    lines = [
        "# Console continuity - briefing unavailable",
        "",
        f"Operator `{OPERATOR}` through binding `{BINDING_ID}`. "
        f"Console session `{console_session}`, {_provenance(opened)}.",
        "",
        f"The briefing could not be built: {_terse(failure)}",
        "",
        "What this session does not know: what landed while this operator was away, "
        "and which threads are open. Nothing here says the journal lost anything.",
        "",
        "This hook does not diagnose the journal; the Record Service owns that rule. "
        "Read it with `python -m soveraeign_record_service.cli --root .local/console/journal`, "
        "with `services/record/src` and `services/console/src` on PYTHONPATH.",
        "",
        "A session close pins the read position the next session starts from. If the "
        "close fails the same way, that position does not advance and the next session "
        "sees this same gap.",
    ]
    if notes:
        lines.extend(["", *notes])
    return "\n".join(lines)


def start(event: dict[str, Any]) -> str:
    """Open or resume the console session for this host session, and brief it.

    Opening and briefing are separate failures. The open commits a record; the
    briefing only reads one. A briefing that cannot be built degrades to a report
    naming what is unknown, rather than taking the whole hook down with it.

    A binding that cannot be written is the same shape read the other way: the
    record has already committed and this hook holds the id, so it says so rather
    than reporting the open as unknown. It also says what that costs, because the
    next start will not find the session and will open a second one.
    """
    host_session = event.get("session_id", "unknown")
    notes: list[str] = []
    try:
        _ensure_grants()
    except ConsoleRefused as failure:
        # Grants are a precondition for recording, not for reading, so a refusal
        # here must not cost the session its briefing. It must also not vanish:
        # this call sits before the try below, so an escaping refusal reached
        # main()'s catch-all and the session got one flat line instead of the
        # provenance, the record-is-intact sentence, and the read instructions.
        # The refusal now travels as a note into whichever report is built.
        notes.append(
            f"Session grants were not established ({_terse(failure)}). This binding "
            f"asked for {', '.join(NEEDED)} on the operator's own store. What follows "
            "is briefed without them, and the open or close below may refuse for the "
            "same reason.")
    bindings = _bindings()
    console_session = bindings.get(host_session)
    opened = False
    if console_session is None:
        console_session = _console("open-session", "--operator", OPERATOR,
                                   "--actor-kind", "MODEL",
                                   "--binding", BINDING_ID)["session_id"]
        opened = True
        try:
            _remember(host_session, console_session)
        except OSError as failure:  # the record committed; only the convenience failed
            notes.append(
                f"The host binding was not saved ({_terse(failure)}). Console session "
                f"`{console_session}` exists and this session is using it, but the next "
                "start will not find it and will open a second one.")
    try:
        return _render(_console("session-context", "--reader", OPERATOR),
                       console_session, notes)
    except Exception as failure:  # a briefing is a read; losing it loses no record
        return _degraded(console_session, opened, failure, notes)


def end(event: dict[str, Any]) -> str:
    """Close the console session so the next one has a read position to start from."""
    console_session = _bindings().get(event.get("session_id", ""))
    if console_session is None:
        return ""
    closed = _console("close-session", "--operator", OPERATOR,
                      "--session", console_session)
    return f"Console session {console_session} closed at cursor {closed['unread_cursor'][:16]}."


def main(argv: list[str]) -> int:
    action = argv[1] if len(argv) > 1 else "start"
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    try:
        output = {"start": start, "end": end}[action](event)
    except Exception as failure:  # never break a session over a missing convenience
        print(f"Console continuity unavailable ({_terse(failure)}). "
              f"Whether the {action} committed a record is unknown from here; "
              "read the journal rather than assuming either way.")
        return 0
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
