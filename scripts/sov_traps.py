#!/usr/bin/env python3
"""Verify that the traps recorded in CLAUDE.md are still real.

A trap is a fact about this repository that actively misleads a reader who has
not met it before: a command that answers confidently and wrongly, a green
result that does not mean what it appears to mean. Each one below cost a session
a false claim or a wasted hour.

Recording them in prose is not enough. Prose about a repository goes stale
silently, and a stale warning is worse than none - it teaches a reader to
distrust the whole file. So each trap that can be checked offline is checked
here, and this command FAILS when a trap stops being true.

That inversion is the point. A failure here does not mean something broke; it
means something was fixed, and the corresponding entry in CLAUDE.md must be
deleted. The warning cannot outlive the hazard.

Traps that need network access are recorded but not asserted because this checker
is deliberately offline and unattended runs carry no `gh`. External effects in
other operations are scoped by live authority rather than refused by phase. They
are listed as ATTENDED so nobody mistakes silence for confirmation.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Trap:
    """One misleading fact, and how to tell whether it still misleads."""

    id: str
    summary: str
    check: Callable[[], tuple[bool, str]] | None  # None => attended only
    fixed_hint: str = ""


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(ROOT), capture_output=True, text=True, check=False,
    )
    return result.stdout if result.returncode == 0 else ""


def _green_is_not_conformance() -> tuple[bool, str]:
    """A passing verification does not mean the specification is met.

    The participant's recorded baseline registers failing requirements as the
    expected result, so the suite is green while conformance is not.
    """
    baseline = ROOT / "services" / "asset" / "conformance" / "BASELINE.md"
    if not baseline.is_file():
        return False, f"{baseline.relative_to(ROOT)} is gone; the baseline convention changed"
    text = baseline.read_text(encoding="utf-8", errors="replace").upper()
    still = "FAIL" in text
    return still, f"BASELINE.md records failing requirements: {still}"


def _negated_standing_tokens() -> tuple[bool, str]:
    """`NOT_WITNESSED` contains the token `WITNESSED`.

    Any check that matches standing by substring reports every one of these as a
    witnessed claim. This trap guards `scripts/sov_standing.py`, which is written
    against it; if the negated spellings ever leave STATUS.yaml, that check's
    defeating case has lost its subject and must be re-grounded.
    """
    status = ROOT / "STATUS.yaml"
    if not status.is_file():
        return False, "STATUS.yaml is gone"
    negated = [
        line.strip()
        for line in status.read_text(encoding="utf-8", errors="replace").split("\n")
        if "_status:" in line and "NOT_WITNESSED" in line
    ]
    return bool(negated), f"{len(negated)} status field(s) spell a negated standing"


TRAPS = (
    Trap(
        id="T2",
        summary="verify.py exit 0 does not mean conformance; the baseline records failing requirements",
        check=_green_is_not_conformance,
        fixed_hint="the baseline no longer records failures - delete this trap from CLAUDE.md",
    ),
    Trap(
        id="T3",
        summary="NOT_WITNESSED contains the token WITNESSED; substring standing checks false-positive",
        check=_negated_standing_tokens,
        fixed_hint="no negated standing spellings remain - re-ground sov_standing.py's defeating case",
    ),
    Trap(
        id="T4",
        summary="branches/main/protection returns 404 while a ruleset is active; query /rulesets instead",
        check=None,
    ),
    Trap(
        id="T5",
        summary="a skipped required check satisfies the ruleset; skipped is not blocked",
        check=None,
    ),
    Trap(
        id="T6",
        summary="several sessions write this tree at once; freeze a commit before witnessing or ratifying",
        check=None,
    ),
)


def main(argv: list[str] | None = None) -> int:
    resolved: list[Trap] = []
    attended = 0
    for trap in TRAPS:
        if trap.check is None:
            attended += 1
            print(f"ATTENDED {trap.id}: {trap.summary}")
            print("         not asserted here - needs attended network observation outside this offline checker")
            continue
        still, evidence = trap.check()
        if still:
            print(f"HOLDS    {trap.id}: {trap.summary}")
            print(f"         {evidence}")
        else:
            resolved.append(trap)
            print(f"RESOLVED {trap.id}: {trap.summary}", file=sys.stderr)
            print(f"         {evidence}", file=sys.stderr)
            print(f"         {trap.fixed_hint}", file=sys.stderr)

    checked = len(TRAPS) - attended
    if resolved:
        print(
            f"\nFAIL: {len(resolved)} trap(s) no longer hold. This is good news and a "
            "required edit: delete the resolved entries from CLAUDE.md so the file "
            "cannot warn about a hazard that is gone.",
            file=sys.stderr,
        )
        return 1
    print(f"\nPASS: {checked} trap(s) still hold, {attended} recorded for attended checking")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
