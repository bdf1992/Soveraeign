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

`sovharness/lexer.py` owns the first reading and states its own limit: it is a lexer, so a
grammar error whose tokens are all well formed passes it.

A grammar reading closes that gap where a JavaScript engine is present, and the mode
matters. `node --check <file>.js` returns zero on these files whatever they contain,
because they open with `export`; it is what was hand-run while two of them were broken.
`node --input-type=module --check` reads the same bytes as a module and rejects them, as
does the same content named `.mjs`. Reproduced on v22.22.2 here and reported on v24.19.0.

The lexer runs always and is what refuses; `AGENTS.md` keeps the required surface
dependency free. The grammar reading runs only where node exists, and its absence is
printed rather than passed over, because a check that quietly skips is a check that
satisfies its own requirement (`CLAUDE.md`, trap T5). Nothing here settles standing.
"""

from __future__ import annotations

from pathlib import Path
import argparse
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from sovharness.lexer import broken_concatenation, unreadable  # noqa: E402

WORKFLOWS = ROOT / ".claude" / "workflows"
NODE_UNAVAILABLE = "node absent: grammar unread, only the lexer refused or passed this file"


def grammar(path: Path) -> str | None:
    """What a JavaScript engine says about this file, read as a module.

    Returns None when the engine accepts it, its complaint when it does not, and
    NODE_UNAVAILABLE when no engine is here. The caller prints that third case; it never
    counts as a clean reading, because a skipped check is not a passed one.
    """
    node = shutil.which("node")
    if not node:
        return NODE_UNAVAILABLE
    done = subprocess.run([node, "--input-type=module", "--check"],
                          input=path.read_bytes(), capture_output=True)
    if done.returncode == 0:
        return None
    first = done.stderr.decode("utf-8", errors="replace").strip().splitlines()
    detail = next((line for line in first if "Error" in line), "rejected by node")
    return f"node reads this as a module and rejects it: {detail.strip()}"


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
    said = grammar(path)
    # An unparseable file the lexer already named does not need naming twice; a top-level
    # `return`, which this harness's runtime wraps, is not a defect in the file.
    if said and said is not NODE_UNAVAILABLE and not cannot_read and "Illegal return" not in said:
        defects.append(said)
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
    unread = grammar(paths[0]) is NODE_UNAVAILABLE
    for path in paths:
        defects = grade(path)
        if defects:
            failing += 1
            print(f"DEFECT {path.name}")
            for defect in defects:
                print(f"       {defect}")
    if unread:
        print(f"NOTE   {NODE_UNAVAILABLE}")
    verdict = "FAIL" if failing else "PASS"
    limit = ("Lexical only: a workflow whose tokens are all well formed and whose meaning "
             "is wrong passes here." if unread else
             "Lexed here and read as a module by node: a file whose grammar holds and "
             "whose meaning is wrong passes here.")
    print(f"{verdict}: {len(paths)} workflow(s) read, {failing} carrying a defect. {limit}")
    return 1 if failing else 0

if __name__ == "__main__":
    raise SystemExit(main())
