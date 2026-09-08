#!/usr/bin/env python3
"""Put the prose rules in front of the session that talks to a person, every turn.

Host plumbing. `.claude/` holds no standing and grants no authority (`AGENTS.md`,
Local orchestration harness). This hook owns no rule; `.claude/skills/unslop/SKILL.md`
owns them and this reads that file at fire time.

Why a hook rather than an instruction. `AGENTS.md` has required `unslop` for
human-facing output since it was written, and a whole session ran without the skill
being invoked once, in a conversation whose entire subject was that the output was
unreadable. The instruction sits in a memory file loaded before a hundred turns of
work and is outranked by every later thing in the window. A launched agent does not
have this problem: `.claude/agents/sov-comms.md` names `unslop` in its `skills` field
and the harness loads the whole skill into its context before it runs. The main
conversation has no such field - an output style takes `name`, `description` and
`keep-coding-instructions`, and cannot preload anything - so the same guarantee has
to come from somewhere else. `UserPromptSubmit` is that somewhere: it fires once per
turn, before the model reads the message, and its `additionalContext` lands in the
window at the position that actually gets read.

What it injects is deliberately short and identical every turn. The skill itself runs
to two screens; pasting it each turn would spend the context it is trying to make
worth reading, and a reminder that changes every turn cannot be skimmed past because
it is never the same, which is a cost with no matching benefit. The compact form
names the pass and points at the file, and the model loads the skill when it needs
the detail.

It must never break a session. Any failure prints nothing and exits 0.
"""

from __future__ import annotations

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / ".claude" / "skills" / "unslop" / "SKILL.md"

#: Read from the skill rather than restated here, so the rules keep one owner
#: (`AGENTS.md`: do not duplicate a rule in another file as a competing authority).
#: The heading is the skill's own; a rename there empties this rather than silently
#: shipping a stale copy, which is the failure a hardcoded duplicate would hide.
SECTION = "## Pass"


def pass_items(text: str) -> list[str]:
    """The numbered steps under the skill's Pass heading, in order."""
    if SECTION not in text:
        return []
    body = text.split(SECTION, 1)[1]
    body = body.split("\n## ", 1)[0]
    items: list[str] = []
    for line in body.splitlines():
        stripped = line.strip()
        if stripped[:1].isdigit() and "." in stripped[:3]:
            items.append(stripped.split(".", 1)[1].strip())
        elif stripped and items:
            # A wrapped continuation of the item above. Without this, the two items
            # the skill happens to wrap arrive cut off mid-clause, which reads as a
            # rule that means something other than what it says.
            items[-1] = f"{items[-1]} {stripped}"
    return items


def reminder(items: list[str]) -> str:
    """The text placed in front of the turn."""
    lines = [
        "unslop is required for human-facing output (AGENTS.md, Human-facing output).",
        "It is not loaded unless you load it. Before you answer, run its pass:",
    ]
    lines += [f"  - {item}" for item in items]
    lines += [
        "",
        "Lead with the outcome. End when the answer ends: no next steps, residuals or",
        "offers that were not asked for. Correct an earlier statement only when the error",
        "changes what the reader does.",
        "",
        f"Full skill: {SKILL.relative_to(ROOT).as_posix()}. "
        "Grade a draft: python scripts/sov_comms.py check -",
    ]
    return "\n".join(lines)


def main() -> int:
    """Emit the reminder as additionalContext, or nothing at all."""
    try:
        items = pass_items(SKILL.read_text(encoding="utf-8"))
    except OSError:
        return 0
    if not items:
        return 0
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": reminder(items),
    }}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BaseException:
        sys.exit(0)
