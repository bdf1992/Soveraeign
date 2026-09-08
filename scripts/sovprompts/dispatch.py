"""Find the calls a workflow makes to an agent, and read what each one is handed.

Separate from rendering because it answers a different question: rendering asks what a
prompt says, this asks which prompts exist and what they splice in. Both are needed to
grade the rule that an evaluator never receives the builder's account as its oracle, and
one module doing both crossed the size ceiling `ENGINEERING.md` sets.

Every reader here works by balancing a call's own parentheses rather than scanning
characters. That distinction is load-bearing: this repository's loop contains
`.replace(/"/g, "'")` and its backlog workflow says "judging agent(s)" in a sentence, and
each defeats a character scan. Three checks were written against a character scan and
withdrawn for exactly that reason.
"""

from __future__ import annotations

import re

from sovprompts.bindings import IDENT, _initialiser, derives_from_agent_result, roots
from sovprompts.render import Unreadable, _body

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


CALL = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*\(")


def resolved_prompt(source: str, prompt: str) -> str:
    """The prompt text, following one level of indirection to where it is written.

    A prompt assembled by a helper is still a prompt, and so is one bound to a name.
    Grading only the call site let one workflow's whole prompt sit outside every check
    because the call read `witnessPrompt(claims, read, tick)`.

    Two shapes are followed. A call `buildPrompt(args)` resolves through the function's
    body. A bare identifier resolves through its `const` initialiser: an independent
    reading found `agent(witnessPrompt, ...)` in `sov-contracts.js` reaching no check at
    all, because only the call shape was followed and a bare name is not a call. Inverting
    that file's label to "oracle and never artifact" left every case passing.
    """
    text = prompt.strip()
    match = CALL.match(text)
    if match and "+" not in prompt.split("(")[0]:
        try:
            return prompt + "\n" + _body(source, match.group(1))
        except Unreadable:
            return prompt
    if IDENT.fullmatch(text):
        initialiser = _initialiser(source, text)
        if initialiser is not None:
            return prompt + "\n" + initialiser
    return prompt


__all__ = [
    "derives_from_agent_result", "dispatches", "interpolated", "prompt_of",
    "resolved_prompt", "roots",
]
