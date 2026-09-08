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


#: The three ways this repository's workflows declare a named function. Only the first was
#: read, so a frame declared `const witnessFrame = function (...) {` was invisible to every
#: rule that reads a frame, while the dispatch rule still saw the call.
DECLARATIONS = (
    r"function\s+{name}\s*\([^)]*\)\s*{{",
    r"\b(?:const|let|var)\s+{name}\s*=\s*(?:async\s+)?function\s*\*?\s*[A-Za-z_$\w]*\s*\([^)]*\)\s*{{",
    r"\b(?:const|let|var)\s+{name}\s*=\s*(?:async\s+)?\([^)]*\)\s*=>\s*{{",
)


def _bindings_of(source: str, name: str) -> int:
    """How many times this source binds `name`: a declaration or a write, either counts.

    JavaScript resolves a call to the binding in force when it runs, and this reader reads
    text. `witnessFrame = function (...)` placed after the declaration, or a second
    `function witnessFrame(...)` that hoisting prefers, both leave the original in the file
    as dead code that every frame rule grades while the evaluator receives the other one.
    An independent reading built both, and `verify.py` stayed at exit 0 with the subject
    pin gone and the build report named the oracle.

    The package already refuses a twice-written binding - `calls._declared_type` refuses a
    name written twice and a duplicate `agentType` key, for this reason - and the rule had
    simply never been applied to the frame itself.
    """
    code = masked(source)
    escaped = re.escape(name)
    sites = {match.start() for match in re.finditer(rf"\bfunction\s+{escaped}\s*\(", code)}
    sites |= {match.start() for match in re.finditer(rf"\b{escaped}\s*=(?!=)", code)}
    return len(sites)


def _body(source: str, name: str) -> str:
    """The source of one function, by brace balance rather than by a text marker."""
    bound = _bindings_of(source, name)
    if bound > 1:
        raise Unreadable(
            f"{name} is bound {bound} times, so which function a call reaches is decided "
            "when it runs and not by the first declaration in the file")
    match = None
    for shape in DECLARATIONS:
        match = re.search(shape.format(name=re.escape(name)), source)
        if match:
            break
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


NESTED = re.compile(r"\bfunction\b[^(){}]*\(|=>\s*")


def _own_returns(code: str) -> list[int]:
    """Where this function's own `return` statements are, with nested functions blanked.

    A return inside `if (...) { ... }` belongs to this function; a return inside a callback
    passed to `.map(function (d) { ... })` does not. Counting both made every workflow with
    an inline callback read as branch-dependent. Length is preserved so offsets stay valid
    in the caller's own text.
    """
    out = list(code)
    for match in NESTED.finditer(code):
        brace = code.find("{", match.end() - 1)
        if brace == -1:
            continue
        index, depth = brace, 0
        while index < len(code):
            if code[index] == "{":
                depth += 1
            elif code[index] == "}":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        for position in range(brace, min(index + 1, len(code))):
            out[position] = " "
    return [match.start() for match in re.finditer(r"\breturn\b", "".join(out))]


def returned(source: str, name: str) -> str:
    """The one expression a function returns, refusing a function that returns more.

    Every return, not the first. A guarded decoy return ahead of the live one was the text
    every frame rule graded while the evaluator received the other: an independent reading
    built `if (legacyFrame) { return [ ...correct frame... ] }` above a return that
    inverted the rule and deleted the subject pin, and both test modules passed. Which
    branch executes is a question this reader does not evaluate, so more than one return
    is refused rather than guessed at.
    """
    body = _body(source, name)
    code = masked(body)
    returns = _own_returns(code)
    if len(returns) != 1:
        raise Unreadable(
            f"{name} has {len(returns)} return statements, so which text reaches an "
            "evaluator depends on a branch this reader does not evaluate")
    return body[returns[0] + len("return"):]
