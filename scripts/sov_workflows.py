#!/usr/bin/env python3
"""Grade the executable harness workflows that nothing else reads.

`.claude/workflows/` holds twenty-three JavaScript files that assemble every prompt this
repository sends an agent. `scripts/lint.py` covers `.md`, `.py`, `.json`, `.yaml`, `.yml`
and `.toml`; `.js` is in none of them, so about four thousand lines of the harness were
graded by nothing at all. A repair made in this repository on 2026-09-08 shipped
`'a' + + 'b'`, which parses cleanly and puts the string `NaN` in the middle of a prompt an
agent then reads as instructions. Only a hand-run syntax check stood between that and a
landing, and a hand-run check is not a check.

Four readings, each of bytes:

    endings      the repository pins LF in .gitattributes, and lint never saw these files
    concat       `'a' + + 'b'`, a syntax-clean expression that yields NaN inside a prompt

Two readings, and the reason there are only two is worth stating once. Three further
checks were written and withdrawn - bracket balance, prose-stripped source, and a count of
dispatches naming no agentType - because each was defeated by the same thing: without
expression context a reader cannot tell a regex literal from division, and cannot tell
`agent(` in code from "judging agent(s)" in a sentence. Both shapes are in this
repository's own workflows. `AGENTS.md` keeps this surface dependency free and a check
that skips when a runtime is absent is not a check (`CLAUDE.md`, trap T5), so no engine is
invoked; that is the ceiling, and a check that reports defects which are not there is
worse than no check at all.

What survives reads bytes and is certain. What it cannot see is everything about meaning:
a workflow that is valid and wrong passes here. Classifying dispatches by a *named* agent
type is sound and is done in `scripts/tests/test_witness_context_provenance.py`, because
asking whether a specific agentType is present excludes the noise that asking "is anything
anonymous" collects. Nothing here settles standing.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovharness.dispatch import broken_concatenation  # noqa: E402

WORKFLOWS = ROOT / ".claude" / "workflows"
def grade(path: Path) -> list[str]:
    """Every defect this reader can see in one workflow."""
    raw = path.read_bytes()
    defects: list[str] = []
    if b"\r\n" in raw:
        defects.append("CRLF line endings; .gitattributes pins LF")
    text = raw.decode("utf-8", errors="replace")
    if broken_concatenation(text):
        defects.append("a concatenation of the shape 'a' + + 'b', which evaluates to NaN "
                       "inside a prompt while parsing cleanly")
    return defects


def main(argv: list[str] | None = None) -> int:
    """Grade every workflow and refuse when any carries a defect."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=WORKFLOWS)
    args = parser.parse_args(argv)
    paths = sorted(args.root.glob("*.js"))
    if not paths:
        print(f"FAIL: no workflow found under {args.root}; this check graded nothing")
        return 1
    failing = 0
    for path in paths:
        defects = grade(path)
        if defects:
            failing += 1
            print(f"DEFECT {path.name}")
            for defect in defects:
                print(f"       {defect}")
    verdict = "FAIL" if failing else "PASS"
    print(f"{verdict}: {len(paths)} workflow(s) read, {failing} carrying a defect. "
          "Structure only: a workflow that is valid and wrong passes here.")
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
