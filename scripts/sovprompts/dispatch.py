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
from sovprompts.render import Unreadable, read, returned
from sovprompts.scan import _balanced, masked


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
    """Where each spliced value sits in a prompt, from the one walk that renders it.

    This used to be a second traversal of the same text, kept in step with
    `render._literals` by hand. Five consecutive independent readings defeated the package
    at a place the two disagreed - a group balanced on raw source here and on the mask
    there, a regex one handled and the other did not, adjacent values counted as one - and
    each repair was another attempt to keep two walks aligned. `render.read` is the walk;
    this is the half of its answer a caller wants.
    """
    return read(prompt)[1]


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
#: `NAME.member` with no call - a getter delivers prose through exactly this shape.
MEMBER_READ = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*(?:\.\s*[A-Za-z_$][\w$]*)+\s*$")


#: JavaScript's own methods on arrays, strings and JSON. A call through one of these on a
#: locally-bound name is a value being shaped, not prose being fetched. Named as what it
#: is - an external vocabulary, not a guess about this repository's intent - and anything
#: outside it that reaches through a local binding is refused rather than rendered opaque.
BUILTIN_METHODS = frozenset({
    "join", "map", "filter", "slice", "concat", "split", "trim", "replace", "toString",
    "keys", "values", "entries", "indexOf", "includes", "reduce", "flatMap", "sort",
    "reverse", "stringify", "parse", "toUpperCase", "toLowerCase", "padStart", "padEnd",
    "repeat", "substring", "charAt", "find", "some", "every", "flat", "at",
})
#: A value reached through a local binding by any route this reader cannot follow: a
#: computed member, an index, a bound method. Each was a defeat: `PC['qa'](d)`, `PA[0](d)`
#: and `PB.qa.bind(null)(d)` each delivered prose the package rendered as one opaque marker.
UNFOLLOWABLE = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*(?:\[[^\]]*\]\s*\(|"
                          r"(?:\.\s*[A-Za-z_$][\w$]*\s*)*\.\s*(?:bind|call|apply)\s*\()")
#: A computed read whose key is a string literal is a member by another spelling, and is
#: resolved as one. A computed read whose key is a name - `DIMENSIONS[d]` - is a lookup in
#: a table, which is a value, and stays one.
COMPUTED_KEY = re.compile(r"^\s*([A-Za-z_$][\w$]*)\s*\[\s*['\"]([A-Za-z_$][\w$]*)['\"]\s*\]")


def _member_source(source: str, root: str, text: str) -> str | None:
    """The expression a `ROOT.member` reference resolves to, or None if it is not a helper.

    None means the receiver is not written as an object carrying that member - a builtin
    on a value - and the reference stays an expression. `Unreadable` means this reader
    cannot establish what it delivers, which is a prompt it cannot read. Independent
    readings reached prose through a plain member, a class method, a getter, a computed
    member, an array index and a bound method; every one rendered as a single marker and
    every check passed.
    """
    member = masked(text).split("(")[0].strip().rsplit(".", 1)[-1].strip() or text.strip()
    if re.search(rf"\bclass\s+{re.escape(root)}\b", masked(source)):
        raise Unreadable(
            f"a witness prompt is built by {root}.{member}, a method of a class this "
            "reader does not follow into, so what the prompt delivers is not readable")
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
    if "(" in masked(text) and member not in BUILTIN_METHODS:
        raise Unreadable(
            f"a witness prompt calls {root}.{member}, which is neither a method JavaScript "
            "defines nor one this reader can follow into a body")
    return None


def _balanced_body(text: str, brace: int) -> str:
    """The inside of the brace that opens at `brace`, balanced on the mask.

    Through the one balancer in `scan.py`, on `masked(text)`, so a `{` or `}` inside a
    string literal is not a brace. This balanced raw source while `render._body` balanced
    the mask, and an independent reading used the difference to reach two refusals this
    package had recorded as pre-empted.
    """
    code = masked(text)
    close = _balanced(code, brace, "{", "}")
    if close == -1:
        raise Unreadable("a prompt helper has no closing brace")
    return text[brace + 1:close]


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
    text = prompt
    # To a fixpoint, bounded. This resolved one hop, so a helper that returned another
    # helper's result delivered everything the second one said through a single opaque
    # marker; an independent reading built two-hop and three-hop chains and both passed.
    for _ in range(8):
        resolved = _resolve_once(source, text)
        if resolved == text:
            return text
        text = resolved
    raise Unreadable(
        "a witness prompt resolves through more indirection than this reader follows, so "
        "what it delivers is not readable")


def _resolve_once(source: str, prompt: str) -> str:
    """One pass of substitution over a prompt expression."""
    out, cut = [], 0
    for begin, finish in expression_spans(prompt):
        text = prompt[begin:finish].strip()
        resolved = None
        unfollowable = UNFOLLOWABLE.match(text)
        if unfollowable and written_into(source, unfollowable.group(1)):
            raise Unreadable(
                "a witness prompt reaches a value through a computed member, an index or a "
                "bound method, which this reader cannot follow: " + text[:60])
        computed = COMPUTED_KEY.match(text)
        if computed and written_into(source, computed.group(1)):
            held = _member_source(source, computed.group(1), computed.group(2) + "(")
            if held is not None:
                resolved = held
        member = MEMBER_CALL.match(text) or MEMBER_READ.match(text)
        if member and resolved is None:
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
