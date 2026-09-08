"""Render what a workflow hands an agent, instead of grading its source text.

A check that reads a declaration where it could measure is the defect this repository
keeps finding in itself. The first witness-context check read the bytes of
`.claude/workflows/sov-loop.js` and matched prose substrings, so the required words could
sit in a comment or a dead constant while the function returned the opposite. An
independent reading defeated it five ways.

This reads the string literals a function returns and joins them the way JavaScript would,
so a comment contributes nothing and a dead constant contributes nothing. An interpolated
expression becomes a marked placeholder, because its value is not knowable from here and
its position is.

No JavaScript engine is used. `AGENTS.md` keeps the test surface dependency free, and a
check that skips when a runtime is missing is not a check (`CLAUDE.md`, T5). What that
costs is stated rather than implied: this understands string literals, concatenation and
array joins, and nothing else. Anything built another way is reported as unreadable rather
than silently passing.
"""

from __future__ import annotations

import re

from sovprompts.scan import masked

EXPR = "<expr>"


class Unreadable(Exception):
    """The source does not use the constructions this reader understands."""


def _literals(source: str) -> str:
    """Join a `'a' + expr + 'b'` chain, keeping literal text and marking expressions."""
    out: list[str] = []
    index, length = 0, len(source)
    pending_expr = False
    while index < length:
        char = source[index]
        if char in "'\"":
            quote, index, buf = char, index + 1, []
            while index < length and source[index] != quote:
                if source[index] == "\\":
                    nxt = source[index + 1] if index + 1 < length else ""
                    buf.append({"n": "\n", "t": "\t"}.get(nxt, nxt))
                    index += 2
                    continue
                buf.append(source[index])
                index += 1
            if index >= length:
                raise Unreadable("unterminated string literal")
            index += 1
            out.append("".join(buf))
            pending_expr = False
            continue
        if char == "/" and index + 1 < length and source[index + 1] in "/*":
            # A comment contributes nothing to what the agent reads, which is the point.
            if source[index + 1] == "/":
                index = source.find("\n", index)
                index = length if index == -1 else index
            else:
                end = source.find("*/", index)
                if end == -1:
                    raise Unreadable("unterminated comment")
                index = end + 2
            continue
        if char.isspace() or char == "+":
            index += 1
            continue
        # Anything else is an expression: consume to the next top-level + or end.
        depth = 0
        start = index
        while index < length:
            here = source[index]
            if here in "([{":
                depth += 1
            elif here in ")]}":
                depth -= 1
            elif here in "'\"" and depth == 0:
                break
            elif here == "+" and depth == 0:
                break
            index += 1
        if index == start:
            raise Unreadable(f"cannot read expression at {source[start:start + 40]!r}")
        if not pending_expr:
            out.append(EXPR)
            pending_expr = True
    return "".join(out)


def _body(source: str, name: str) -> str:
    """The source of one function, by brace balance rather than by a text marker."""
    match = re.search(rf"function\s+{re.escape(name)}\s*\([^)]*\)\s*{{", source)
    if not match:
        raise Unreadable(f"no function named {name!r}")
    index, depth = match.end() - 1, 0
    while index < len(source):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[match.end():index]
        index += 1
    raise Unreadable(f"{name} has no closing brace")


def blocks(source: str, name: str) -> list[str]:
    """The blocks a `return [ ... ].join(...)` function produces, in order."""
    body = _body(source, name)
    start = body.find("return [")
    if start == -1:
        raise Unreadable(f"{name} does not return an array of blocks")
    index, depth = start + len("return "), 0
    while index < len(body):
        if body[index] == "[":
            depth += 1
        elif body[index] == "]":
            depth -= 1
            if depth == 0:
                break
        index += 1
    else:
        raise Unreadable(f"{name}'s return array is unterminated")
    inner = body[start + len("return ["):index]
    # Where the separating commas are is a structural question, and it is answered on the
    # one mask rather than by a scan of this module's own. This split used to be a private
    # character scan that did not skip comments, so a comma inside `/* first, always */`
    # broke one block into two and convicted legal JavaScript. `masked` preserves length,
    # so every offset below is valid in `inner` itself.
    code = masked(inner)
    parts, depth, cut = [], 0, 0
    for position, char in enumerate(code):
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append(inner[cut:position])
            cut = position + 1
    parts.append(inner[cut:])
    return [_literals(part) for part in parts if part.strip()]


def rendered(source: str, name: str) -> str:
    """Everything the function's blocks say, joined."""
    return "\n\n".join(blocks(source, name))

