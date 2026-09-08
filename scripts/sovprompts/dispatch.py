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

from sovprompts.bindings import IDENT, derives_from_agent_result, roots, written_into
from sovprompts.calls import agent_calls
from sovprompts.render import Unreadable, _body


def dispatches(source: str, agent_type: str) -> list[str]:
    """Every dispatch in this source that reaches the named agent type.

    Built on `agent_calls`, which reports a dispatch it cannot classify rather than
    dropping it. This returns only the matching ones; a caller that needs to know about
    the unclassifiable ones asks `agent_calls` directly, and
    `test_witness_context_provenance` fails the build on any of them.
    """
    return [call for call, kind in agent_calls(source) if kind == agent_type]


def prompt_of(call: str) -> str:
    """The prompt expression of an agent(...) call: everything before its options object."""
    depth, quote = 0, ""
    for index, char in enumerate(call):
        if quote:
            if char == quote and call[index - 1:index] != "\\":
                quote = ""
            continue
        if char in "'\"`":
            # Backticks included. Without them a template-literal prompt was read only as
            # far as its first `${`, so a label in the head satisfied the rule while the
            # tail the evaluator actually reads was never graded.
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
        written = written_into(source, text)
        if written:
            return prompt + "\n" + "\n".join(written)
    return prompt


__all__ = [
    "derives_from_agent_result", "dispatches", "interpolated", "prompt_of",
    "resolved_prompt", "roots",
]
