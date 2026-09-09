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

from sovprompts.bindings import (
    IDENT, _split_arguments, derives_from_agent_result, roots, written_into,
)
from sovprompts.calls import _object_member, agent_calls
from sovprompts.frames import array_join_source
from sovprompts.render import Unreadable, returned
from sovprompts.scan import masked


def dispatches(source: str, agent_type: str) -> list[str]:
    """Every dispatch in this source that reaches the named agent type.

    Built on `agent_calls`, which reports a dispatch it cannot classify rather than
    dropping it. This returns only the matching ones; a caller that needs to know about
    the unclassifiable ones asks `agent_calls` directly, and
    `test_witness_context_provenance` fails the build on any of them.
    """
    return [call for call, kind in agent_calls(source) if kind == agent_type]


def prompt_of(call: str) -> str:
    """The prompt argument of an agent(...) call: every argument before its options object.

    Read as arguments, not as characters. This used to return `call[:index]` at the first
    `{` seen at depth zero, on the assumption that the first brace opens the options
    object. An independent reading defeated that with one ordinary object literal inside
    the prompt expression - `'...' + {sep: ' '}.sep + '...'` - which ended the graded text
    early and put an inversion, a real `agent(...)` result, and every splice after it
    outside every rule in this package. A regex containing `{` does the same. Which
    argument is which is structural, so it is answered structurally.

    Fails closed. A call whose last argument is not an object literal is a shape this
    reader does not understand, and `Unreadable` says so rather than grading a guess.
    """
    arguments = _split_arguments(call)
    if len(arguments) != 2:
        raise Unreadable(
            f"an agent call passes {len(arguments)} argument(s); this reader knows the "
            "prompt-then-options shape and refuses to guess which one is the prompt")
    return arguments[0]


def expression_spans(prompt: str) -> list[tuple[int, int]]:
    """Where each spliced expression sits in a prompt, with its literal prose skipped.

    Offsets rather than text, so a caller that needs to substitute a resolved body back in
    can do it without moving anything else. `interpolated` is the same walk reported as
    text.
    """
    out: list[tuple[int, int]] = []
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
        if prompt[start:index].strip():
            out.append((start, index))
    return out


def interpolated(prompt: str) -> list[str]:
    """The expressions a prompt splices in, with its literal prose removed.

    A prompt that happens to contain the word "claims" in a sentence is not handing an
    evaluator the builder's account; a prompt that splices `claims` in is. Grading prose
    for that distinction is what made the first version of this check unreliable.
    """
    return [prompt[a:b].strip() for a, b in expression_spans(prompt)]


CALL = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*\(")
#: `NAME.member(...)` - a call this reader cannot follow into a body.
MEMBER_CALL = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*(?:\.\s*[A-Za-z_$][\w$]*)+\s*\(")


def _member_source(source: str, root: str, text: str) -> str | None:
    """The expression a `ROOT.member(...)` call resolves to, or None if it is not a helper.

    None means the receiver is not written as an object carrying that member - a builtin
    on a value - and the call stays an expression. `Unreadable` means it is such an object
    and this reader cannot follow what it holds, which is a prompt it cannot read.
    """
    member = text.split("(")[0].strip().rsplit(".", 1)[-1].strip()
    for written in written_into(source, root):
        value = _object_member(written, member)
        if value is None:
            continue
        body = value.strip()
        if body.startswith("function") or "=>" in masked(body).split("{")[0]:
            brace = masked(body).find("{")
            if brace != -1:
                return _balanced_body(body, brace)
        raise Unreadable(
            f"a witness prompt is built through {root}.{member}, which this reader cannot "
            "follow into a body, so what the prompt delivers is not readable")
    return None


def _balanced_body(text: str, brace: int) -> str:
    """The inside of the brace that opens at `brace`, balanced on the mask.

    On `masked(text)`, so a `{` or `}` inside a string literal is not a brace. This
    balanced raw source while `render._body` balanced the mask - one question, two answers
    - and an independent reading used the difference to reach two refusals this package
    had recorded as pre-empted by the readability gate, on JavaScript that gate accepts.
    """
    code = masked(text)
    index, depth = brace, 0
    while index < len(code):
        if code[index] == "{":
            depth += 1
        elif code[index] == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1:index]
        index += 1
    raise Unreadable("a prompt helper has no closing brace")


def resolved_prompt(source: str, prompt: str) -> str:
    """The prompt with every indirection inside it replaced by the text it resolves to.

    A prompt assembled by a helper is still a prompt, and so is one bound to a name.
    Grading only the call site let one workflow's whole prompt sit outside every check
    because the call read `witnessPrompt(claims, read, tick)`.

    Every piece, not the whole expression. This used to match the prompt against `CALL`
    and `IDENT.fullmatch`, both of which require the prompt to be *exactly* one call or
    exactly one name. Twenty-one of the twenty-two repaired workflows concatenate -
    `'...label...' + qaPrompt(d)` - which is neither, so the helper body was rendered as
    one opaque `<expr>` and its text never read. An independent reading put the corpus's
    own "oracle and never artifact" sentence inside such a helper and every case passed.

    Substituted in place rather than appended. Appending resolved bodies after the prompt
    puts the helper's literals behind every splice at the call site, and the position rule
    counts `<expr>` markers in delivered order; the resolved text has to keep the order
    the evaluator reads in.
    """
    out, cut = [], 0
    for begin, finish in expression_spans(prompt):
        text = prompt[begin:finish].strip()
        resolved = None
        member = MEMBER_CALL.match(text)
        if member:
            # A prompt built by a call through a name this file binds. `changedFiles.join(', ')`
            # is a builtin on a value and stays an expression; `PROMPTS.qa(d, account)` is a
            # helper holding prose, and it matched neither the call shape nor the bare-name
            # shape, so a whole prompt rendered as one `<expr>` with the package's own
            # inversion sentence inside it, unread by either grader. An independent reading
            # built exactly that. The two are told apart by asking whether the receiver is
            # written as an object carrying that member.
            held = _member_source(source, member.group(1), text)
            if held is not None:
                resolved = held
        match = CALL.match(text)
        if match and "+" not in text.split("(")[0]:
            try:
                resolved = returned(source, match.group(1))
            except Unreadable as defect:
                # A name that is not a local function - `JSON.stringify`, an import - is
                # not indirection this reader has to follow, and stays an expression. A
                # helper it *can* find and cannot read is different: the text an evaluator
                # receives is then branch-dependent one level down, which is the defeat
                # this package refuses at the top level, so it is refused here too.
                if not str(defect).startswith("no function named"):
                    raise
                resolved = None
            if resolved is not None:
                # A function returning `[a, b].join(sep)` is a frame. Substituted as the
                # concatenation `a + b`, because splicing the array source itself puts a
                # bare `[` where a string belongs and renders the whole thing as one
                # opaque expression - which is how a helper-built frame telling an
                # evaluator not to pin its subject reached no rule at all.
                joined = array_join_source(resolved)
                if joined is not None:
                    resolved = joined
        elif IDENT.fullmatch(text):
            written = written_into(source, text)
            resolved = "\n".join(written) if written else None
        if resolved is None:
            continue
        out.append(prompt[cut:begin])
        out.append(resolved)
        cut = finish
    out.append(prompt[cut:])
    return "".join(out)


__all__ = [
    "derives_from_agent_result", "dispatches", "interpolated", "prompt_of",
    "resolved_prompt", "roots",
]
