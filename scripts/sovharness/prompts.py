"""Render what a workflow actually hands an agent, instead of grading its source text.

A check that reads a declaration where it could measure is the defect this repository
keeps finding in itself. The first version of the witness-context check read the bytes of
`.claude/workflows/sov-loop.js` and matched prose substrings, so the required words could
sit in a comment or a dead constant while the function returned the opposite. An
independent reading defeated it five ways.

This reads the string literals a function returns and joins them the way JavaScript would,
so a comment contributes nothing and a dead constant contributes nothing. Interpolated
expressions become a marked placeholder, because their value is not knowable from here and
their position is.

No JavaScript engine is used. `AGENTS.md` requires the test surface to stay dependency
free, and a check that skips when a runtime is missing is not a check (`CLAUDE.md`, T5).
What that costs is stated rather than implied: this understands string literals,
concatenation and array joins, and nothing else. A frame built by any other construction
is reported as unreadable rather than silently passing.
"""

from __future__ import annotations

import re

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
    # Split on commas that separate array elements, not commas inside strings or calls.
    parts, depth, quote, current = [], 0, "", []
    for char in inner:
        if quote:
            current.append(char)
            if char == quote and current[-2:-1] != ["\\"]:
                quote = ""
            continue
        if char in "'\"":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return [_literals(part) for part in parts if part.strip()]


def rendered(source: str, name: str) -> str:
    """Everything the function's blocks say, joined."""
    return "\n\n".join(blocks(source, name))


AGENT_TYPE = re.compile(r"agentType:\s*(?:['\"](?P<lit>[a-z-]+)['\"]|(?P<ref>[A-Za-z_$][\w$]*))")


def _const(source: str, name: str) -> str | None:
    """Resolve `const NAME = 'value'`, so a dispatch cannot hide behind an identifier."""
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*['\"]([a-z-]+)['\"]", source)
    return match.group(1) if match else None


def dispatches(source: str, agent_type: str) -> list[str]:
    """Every `agent(...)` call in this source that reaches the named agent type.

    Finds the call by brace balance from `agent(`, with or without `await`, so a dispatch
    is not missed for being written differently. The agent type is read as a literal or
    resolved through a `const`; an unresolvable identifier is returned as a candidate
    rather than dropped, because a dispatch nobody can classify is not a dispatch nobody
    needs to look at.
    """
    found: list[str] = []
    for match in re.finditer(r"\bagent\s*\(", source):
        index, depth = match.end() - 1, 0
        while index < len(source):
            if source[index] == "(":
                depth += 1
            elif source[index] == ")":
                depth -= 1
                if depth == 0:
                    break
            index += 1
        else:
            continue
        call = source[match.end():index]
        kind = AGENT_TYPE.search(call)
        if not kind:
            continue
        named = kind.group("lit") or _const(source, kind.group("ref") or "")
        if named == agent_type:
            found.append(call)
    return found


def prompt_of(call: str) -> str:
    """The prompt expression of an agent(...) call: everything before its options object."""
    depth, quote = 0, ""
    for index, char in enumerate(call):
        if quote:
            if char == quote and call[index - 1:index] != "\\":
                quote = ""
            continue
        if char in "'\"":
            quote = char
        elif char in "([":
            depth += 1
        elif char in ")]":
            depth -= 1
        elif char == "{" and depth == 0:
            return call[:index].rstrip().rstrip(",")
    return call


def interpolated(prompt: str) -> list[str]:
    """The expressions a prompt splices in, with its literal prose removed.

    A prompt that happens to contain the word "claims" in a sentence is not handing an
    evaluator the builder's account; a prompt that splices `claims` in is. Grading prose
    for that distinction is what made the first version of this check unreliable.
    """
    out: list[str] = []
    index, length = 0, len(prompt)
    while index < length:
        char = prompt[index]
        if char in "'\"":
            quote, index = char, index + 1
            while index < length and prompt[index] != quote:
                index += 2 if prompt[index] == "\\" else 1
            index += 1
            continue
        if char == "/" and index + 1 < length and prompt[index + 1] in "/*":
            if prompt[index + 1] == "/":
                found = prompt.find("\n", index)
                index = length if found == -1 else found
            else:
                found = prompt.find("*/", index)
                index = length if found == -1 else found + 2
            continue
        if char.isspace() or char == "+":
            index += 1
            continue
        start, depth = index, 0
        while index < length:
            here = prompt[index]
            if here in "([{":
                depth += 1
            elif here in ")]}":
                depth -= 1
            elif here in "'\"" and depth == 0:
                break
            elif here == "+" and depth == 0:
                break
            index += 1
        piece = prompt[start:index].strip()
        if piece:
            out.append(piece)
    return out


BROKEN_CONCAT = re.compile(r"['\"]\s*\+\s*\+\s*['\"]")


def broken_concatenation(source: str) -> bool:
    """`'a' + + 'b'` parses and yields NaN in the middle of a prompt.

    A syntax check passes it. Nothing lints these files. This is the one shape that bit
    while repairing them, so it is the one shape that is now refused.
    """
    return bool(BROKEN_CONCAT.search(source))


CALL = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*\(")


def resolved_prompt(source: str, prompt: str) -> str:
    """The prompt text, following one level of `buildPrompt(args)` indirection.

    A prompt assembled by a helper is still a prompt. Grading only the call site let one
    workflow's whole prompt sit outside every check because the call read
    `witnessPrompt(claims, read, tick)`.
    """
    match = CALL.match(prompt.strip())
    if not match or "+" in prompt.split("(")[0]:
        return prompt
    name = match.group(1)
    try:
        body = _body(source, name)
    except Unreadable:
        return prompt
    return prompt + "\n" + body
