#!/usr/bin/env python3
"""Grade the executable harness workflows that nothing else reads.

`.claude/workflows/` holds twenty-three JavaScript files that assemble every prompt this
repository sends an agent. `scripts/lint.py` covers `.md`, `.py`, `.json`, `.yaml`, `.yml`
and `.toml`; `.js` is in none of them, so about four thousand lines of the harness were
graded by nothing at all.

An earlier version of this file shipped two byte-level readings and recorded a ceiling as
the reason there were not more: that without expression context a reader cannot tell a
regex literal from division, so string termination and bracket balance could not be
graded. That was convenient rather than true. An independent reading refuted it in about
ninety lines of standard library, and while the claim stood, two of the twenty-three files
were unparseable JavaScript that this check reported as clean - `sov-trust.js` closed a
string on the apostrophe in "workflow's", and `sov-coldstart.js` held three strings broken
across raw newlines. Both are documented launch paths. A false all-clear is worse than the
silence it replaced.

Three readings now, each of what the file is rather than what anyone says about it:

    readable     it lexes as JavaScript: strings close, brackets match their openers
    endings      the repository pins LF in .gitattributes, and lint never saw these files
    concat       `'a' + + 'b'`, a syntax-clean expression that yields NaN inside a prompt

`sovharness/lexer.py` owns the reading and states its own limit: it is a lexer, so a
grammar error whose tokens are all well formed passes here. `node --check` is not a
substitute and was the thing that missed both defects - these files open with `export`,
so it parses them as scripts and reports nothing. `AGENTS.md` keeps this surface
dependency free and a check that skips when a runtime is absent is not a check
(`CLAUDE.md`, trap T5), so no engine is invoked here either. Nothing here settles standing.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovharness.lexer import broken_concatenation, unreadable  # noqa: E402

WORKFLOWS = ROOT / ".claude" / "workflows"
def grade(path: Path) -> list[str]:
    """Every defect this reader can see in one workflow."""
    raw = path.read_bytes()
    defects: list[str] = []
    if b"\r\n" in raw:
        defects.append("CRLF line endings; .gitattributes pins LF")
    text = raw.decode("utf-8", errors="replace")
    cannot_read = unreadable(text)
    if cannot_read:
        defects.append(cannot_read)
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
          "Lexical only: a workflow whose tokens are all well formed and whose meaning "
          "is wrong passes here.")
    return 1 if failing else 0

if __name__ == "__main__":
    raise SystemExit(main())
