#!/usr/bin/env python3
"""Tell a starting session what work has been left where nothing else will find it.

Host plumbing. `.claude/` holds no standing and grants no authority (`AGENTS.md`,
Local orchestration harness). Every judgement here is made by `scripts/sov_strand.py`,
which reads git directly and is runnable and testable on its own; this file only carries
its short reading into the session's opening context.

Why at session start rather than in `scripts/verify.py`: stranded work is a property of
one machine's working area, not of the repository. A fresh clone has none of it and would
pass a gate that means nothing there, while a shared tree would fail one session's gate
for another session's branch. The reading belongs where somebody sees it without asking,
and nowhere that blocks anyone.

It speaks only when a commit exists in no other copy, because that is the only condition
here that loses work. Untidy is reported underneath it and never on its own.

It must never break a session. Any failure prints nothing and exits 0.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def main() -> int:
    """Print the short stranded-work reading, or nothing at all."""
    try:
        import sov_strand

        reading = sov_strand.brief()
    except Exception:  # noqa: BLE001 - a hook must never break a session
        return 0
    if reading:
        print(reading)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
