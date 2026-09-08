"""Find the agent dispatches in a workflow and say which agent each one reaches.

Split from `dispatch.py` at the line ceiling. That module reads what a dispatch is
handed; this one decides which dispatches exist at all, which is a different question and
the one three independent readings kept defeating.

This fails closed. `agent_calls` reports a dispatch whose agent type it cannot read as
`None`, and the caller treats that as a defect. The previous enumerator returned only the
calls whose type it matched, so four constructions - `agentType: KIND.witness`, a
concatenated type, an options object held in a `const`, and a call through `const spawn =
agent` - were dropped without trace and their prompts sat outside every rule.

Two scanning hazards are handled here because both silently remove work from the check
rather than adding it, and both were found by measurement after being written wrongly
first: an apostrophe inside a `//` comment, and a quote inside a regular expression. The
second desynchronised the scan for the rest of `sov-loop.js`, so every dispatch below
line 415 stopped existing.
"""

from __future__ import annotations

import re

from sovprompts.bindings import IDENT, _split_arguments, _without_strings, written_into
from sovprompts.render import EXPR, _literals

AGENT_TYPE = re.compile(r"agentType:\s*(?:['\"](?P<lit>[a-z-]+)['\"]|(?P<ref>[A-Za-z_$][\w$]*))")


def _const(source: str, name: str) -> str | None:
    """Resolve `const NAME = 'value'`, so a dispatch cannot hide behind an identifier."""
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*['\"]([a-z-]+)['\"]", source)
    return match.group(1) if match else None


#: A `/` here opens a regular expression rather than dividing. Standard JavaScript
#: disambiguation: a regex may follow an operator or an opening bracket, never a value.
BEFORE_REGEX = set("(,=:[!&|?{};+-*%~^<>") | {""}
BEFORE_REGEX_WORDS = frozenset({
    "return", "typeof", "case", "in", "of", "new", "delete", "void", "throw", "do", "else",
})


def _opens_regex(source: str, index: int) -> bool:
    """Whether the `/` at `index` starts a regex literal rather than a division."""
    back = index - 1
    while back >= 0 and source[back] in " \t\r\n":
        back -= 1
    if back < 0:
        return True
    if source[back] in BEFORE_REGEX:
        return True
    word = ""
    while back >= 0 and (source[back].isalnum() or source[back] in "_$"):
        word = source[back] + word
        back -= 1
    return word in BEFORE_REGEX_WORDS


def _string_spans(source: str) -> list[tuple[int, int]]:
    """Where the string literals are, so prose is not enumerated as code.

    This repository's backlog workflow says "judging agent(s)" in a sentence. Enumerating
    the raw bytes reads that as a dispatch.

    Comments and regular expressions are skipped before strings, and both were found the
    hard way. An apostrophe in `// the grant's budget` opens a span that swallows the next
    lines of code. And `.replace(/"/g, "'")` in `sov-loop.js` puts a quote inside a regex:
    reading it as a string opener desynchronised the scan for the remaining 1,800
    characters of the file, so every dispatch below it stopped existing. Both failures are
    silent and both remove work from the check rather than adding it, which is why this
    scanner is written against the two constructions that defeat it rather than against
    the common case.
    """
    spans: list[tuple[int, int]] = []
    index, length = 0, len(source)
    while index < length:
        char = source[index]
        if char == "/" and index + 1 < length and source[index + 1] in "/*":
            if source[index + 1] == "/":
                found = source.find("\n", index)
            else:
                found = source.find("*/", index)
                found = found + 2 if found != -1 else -1
            index = length if found == -1 else found
            continue
        if char == "/" and _opens_regex(source, index):
            index += 1
            in_class = False
            while index < length:
                here = source[index]
                if here == "\\":
                    index += 2
                    continue
                if here == "[":
                    in_class = True
                elif here == "]":
                    in_class = False
                elif here == "/" and not in_class:
                    break
                elif here == "\n":
                    break
                index += 1
            index += 1
            continue
        if char in "'\"`":
            quote, start = char, index
            index += 1
            while index < length and source[index] != quote:
                index += 2 if source[index] == "\\" else 1
            spans.append((start, min(index, length - 1)))
        index += 1
    return spans


def _inside(spans: list[tuple[int, int]], position: int) -> bool:
    return any(start <= position <= end for start, end in spans)


def _agent_names(source: str) -> set[str]:
    """`agent` and every name bound to it.

    `const spawn = agent` followed by `spawn(...)` was a dispatch no sweep saw, because
    the enumerator matched the literal text `agent(`. This module resolved bindings for
    every name except the name of the function it enumerates.
    """
    names = {"agent"}
    for match in re.finditer(
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*agent\s*(?![\w$(])", source):
        names.add(match.group(1))
    return names


def _object_member(text: str, key: str) -> str | None:
    """The value of `key:` inside an object literal, read to its top-level comma."""
    match = re.search(rf"\b{re.escape(key)}\s*:\s*", text)
    if not match:
        return None
    index, depth = match.end(), 0
    while index < len(text):
        char = text[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif char == "," and depth == 0:
            break
        index += 1
    return text[match.end():index].strip()


def _resolve_literal(source: str, expr: str, depth: int = 0) -> str | None:
    """An expression's string value, or None when this reader cannot establish one.

    None is the honest answer and the caller must treat it as a defect rather than as
    "not a witness". Four constructions reached a witness through an `agentType` this
    could not read, and each was silently dropped instead of reported.
    """
    text = expr.strip()
    if depth > 4 or not text:
        return None
    try:
        joined = _literals(text)
    except Exception:
        joined = None
    if joined and EXPR not in joined:
        return joined.strip()
    member = re.fullmatch(r"([A-Za-z_$][\w$]*)\s*\.\s*([A-Za-z_$][\w$]*)", text)
    if member:
        for written in written_into(source, member.group(1)):
            value = _object_member(written, member.group(2))
            if value is not None:
                return _resolve_literal(source, value, depth + 1)
        return None
    if IDENT.fullmatch(text):
        for written in written_into(source, text):
            value = _resolve_literal(source, written, depth + 1)
            if value is not None:
                return value
    return None


def agent_calls(source: str) -> list[tuple[str, str | None]]:
    """Every agent dispatch in this source, with the agent type it reaches or None.

    None means unresolvable, not absent. The previous enumerator returned only calls
    whose type matched, so `agentType: KIND.witness`, `'sov-' + 'witness'`, an options
    object held in a `const`, and a dispatch through an alias of `agent` were each
    dropped without trace. A check that cannot classify a dispatch must say so; treating
    it as someone else's dispatch is how four witness prompts sat outside every rule.
    """
    found: list[tuple[str, str | None]] = []
    spans = _string_spans(source)
    for name in sorted(_agent_names(source)):
        for match in re.finditer(rf"\b{re.escape(name)}\s*\(", source):
            if _inside(spans, match.start()):
                continue
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
            found.append((call, _declared_type(source, call)))
    return found


def _declared_type(source: str, call: str) -> str | None:
    """The agent type a call reaches, or None when this cannot be established.

    None covers two different failures and must cover both. "I cannot read this" was the
    first: four constructions removed a prompt from every rule by declaring a type this
    could not resolve. "I can read this two ways" was the second, and it defeated the
    repair for the first:

        let OPTS = { agentType: 'sov-worker' }
        const built = await agent('build', OPTS)
        OPTS = { agentType: 'sov-' + 'witness', phase: 'Witness' }
        const w = await agent('THE BUILD REPORT IS YOUR ORACLE: ' + built.summary, OPTS)

    Both calls read `sov-worker`, because every write into `OPTS` was searched and the
    first `agentType` found won. A confident wrong answer is worse than no answer: it
    passes the classifiable check and removes the dispatch from the witness sweep at the
    same time, so the two guards defeat each other.

    An inline declaration in the call itself is unambiguous and is preferred. Otherwise
    every write into the options binding is resolved, and anything but exactly one
    distinct answer is None.
    """
    inline = re.search(r"agentType\s*:\s*", call)
    if inline:
        return _resolve_literal(source, _object_member(call[inline.start():], "agentType") or "")
    answers: set[str] = set()
    unreadable = False
    for argument in _split_arguments(call)[1:]:
        name = argument.strip()
        if not IDENT.fullmatch(name):
            continue
        for written in written_into(source, name):
            declared = re.search(r"agentType\s*:\s*", written)
            if not declared:
                continue
            value = _resolve_literal(
                source, _object_member(written[declared.start():], "agentType") or "")
            if value is None:
                unreadable = True
            else:
                answers.add(value)
    if unreadable or len(answers) != 1:
        return None
    return answers.pop()


