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

from functools import lru_cache
import re

from sovprompts.bindings import (
    IDENT, _split_arguments, _statement, _without_strings, written_into,
)
from sovprompts.scan import masked
from sovprompts.render import EXPR, _literals

AGENT_TYPE = re.compile(r"agentType:\s*(?:['\"](?P<lit>[a-z-]+)['\"]|(?P<ref>[A-Za-z_$][\w$]*))")


def _const(source: str, name: str) -> str | None:
    """Resolve `const NAME = 'value'`, so a dispatch cannot hide behind an identifier."""
    match = re.search(rf"const\s+{re.escape(name)}\s*=\s*['\"]([a-z-]+)['\"]", source)
    return match.group(1) if match else None


@lru_cache(maxsize=None)
def _writes_by_name(source: str) -> dict[str, tuple[str, ...]]:
    """Every binding in this source mapped to the expressions written into it, in one pass.

    Built once rather than by scanning the whole file for each candidate name. The
    name-at-a-time form was correct and cost a second per workflow, which the defeats
    corpus turned into forty seconds of the verification budget.
    """
    out: dict[str, list[str]] = {}
    code = masked(source)
    for pattern in (r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*",
                    r"\b([A-Za-z_$][\w$]*)\s*=(?!=)\s*"):
        for match in re.finditer(pattern, code):
            out.setdefault(match.group(1), []).append(_statement(source, match.end()))
    for match in re.finditer(r"\b(?:const|let|var)\s*[{\[]([^}\]]*)[}\]]\s*=\s*", code):
        written = _statement(source, match.end())
        for piece in match.group(1).split(","):
            name = piece.strip().split(":")[-1].strip()
            if IDENT.fullmatch(name or ""):
                out.setdefault(name, []).append(written)
    for match in re.finditer(r"([A-Za-z_$][\w$]*)\s*:\s*([A-Za-z_$][\w$]*)\s*(?![\w$(])", code):
        out.setdefault(match.group(1), []).append(match.group(2))
    return {name: tuple(writes) for name, writes in out.items()}


@lru_cache(maxsize=None)
def _agent_names(source: str) -> frozenset[str]:
    """`agent` and every name bound to it, however many hops away.

    `const spawn = agent` followed by `spawn(...)` was a dispatch no sweep saw, because
    the enumerator matched the literal text `agent(`: this module resolved bindings for
    every name except the name of the function it enumerates. A one-hop regex closed that
    and left five more open - a two-hop alias, a bare reassignment, a member call, a
    destructured alias, and `agent` held as an object member. A call that is never
    recognised produces no refusal, so failing closed cannot reach it, which is why this
    has to be resolution to a fixpoint rather than a pattern.
    """
    writes = _writes_by_name(source)
    names = {"agent"}
    changed = True
    while changed:
        changed = False
        for name, written in writes.items():
            if name in names:
                continue
            for expression in written:
                candidate = expression.strip().rstrip(";").strip()
                # `const oV = { a: agent }` then `const bV = oV.a` reads the member back
                # out. Four alias shapes were closed case by case and the class came back
                # one hop further; the member a write ends on is resolved rather than the
                # write compared whole. The enumerator failed closed on the agent type and
                # open on the callee, and a callee it never recognises produces no refusal.
                tail = candidate.rsplit(".", 1)[-1].strip() if "." in candidate else candidate
                if candidate in names or tail in names:
                    names.add(name)
                    changed = True
                    break
    return frozenset(names)


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
        # Every write, not the first. `let kind = 'sov-worker'` then
        # `kind = 'sov-' + 'witness'` classified a real witness dispatch as a worker while
        # `_declared_type` claimed the ambiguity rule ran everywhere. It did not run here.
        answers = {value for written in written_into(source, text)
                   if (value := _resolve_literal(source, written, depth + 1)) is not None}
        if len(answers) == 1:
            return answers.pop()
    return None


@lru_cache(maxsize=None)
def agent_calls(source: str, permissive: bool = False) -> tuple[tuple[str, str | None], ...]:
    """Every agent dispatch in this source, with the agent type it reaches or None.

    None means unresolvable, not absent. The previous enumerator returned only calls
    whose type matched, so `agentType: KIND.witness`, `'sov-' + 'witness'`, an options
    object held in a `const`, and a dispatch through an alias of `agent` were each
    dropped without trace. A check that cannot classify a dispatch must say so; treating
    it as someone else's dispatch is how four witness prompts sat outside every rule.
    """
    found: list[tuple[str, str | None]] = []
    # Enumerated over the mask and sliced out of the source. `masked` preserves length,
    # so every offset is valid in both, and prose cannot match because it is blanked -
    # this repository's backlog workflow says "judging agent(s)" in a sentence.
    code = masked(source, permissive)
    for name in sorted(_agent_names(source)):
        for match in re.finditer(rf"\b{re.escape(name)}\s*(?:\.\s*(?:call|apply)\s*)?\(", code):
            index, depth = match.end() - 1, 0
            while index < len(code):
                if code[index] == "(":
                    depth += 1
                elif code[index] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                index += 1
            else:
                continue
            call = source[match.end():index]
            found.append((call, _declared_type(source, call)))
    return found


def _types_in(source: str, text: str) -> tuple[set[str], bool]:
    """Every agent type declared in one piece of source, and whether any was unreadable.

    Every occurrence, not the first. `_object_member` returned the first `agentType:` it
    found, and JavaScript takes the last, so a duplicate key inside one object literal
    read as the type it overrides:

        { agentType: 'sov-worker', agentType: 'sov-' + 'witness', phase: 'Witness' }

    node evaluates that to `sov-witness`; the classifier called it a worker and the
    dispatch left the witness sweep. Reading them all and refusing to choose is the same
    rule this module already applies to a binding written twice.
    """
    answers: set[str] = set()
    unreadable = False
    for match in re.finditer(r"agentType\s*:\s*", text):
        value = _resolve_literal(source, _object_member(text[match.start():], "agentType") or "")
        if value is None:
            unreadable = True
        else:
            answers.add(value)
    return answers, unreadable


def _declared_type(source: str, call: str) -> str | None:
    """The agent type a call reaches, or None when this cannot be established.

    None covers three failures and must cover all of them, because each was found by a
    reading that had defeated the repair for the one before it.

    "I cannot read this" was the first: four constructions removed a prompt from every
    rule by declaring a type this could not resolve.

    "I can read this two ways" was the second. A stale write into a reused options binding
    classified a witness dispatch as a worker, which passed the classifiable check and
    emptied the witness sweep at once, so each guard was defeated by the half the other
    would have caught.

    The third was the second again, in the place the rule had not been applied: an inline
    declaration was preferred and then trusted without being checked for ambiguity. A
    duplicate key is legal JavaScript and the classifier read the overridden half. The
    rule now runs everywhere rather than on the path that happened to be repaired.
    """
    if "..." in _without_strings(call):
        # A spread contributes keys this reader cannot see and JavaScript applies in
        # order, so a decoy before it wins here and loses at runtime:
        #   { agentType: 'sov-worker', ...REAL, phase: 'Witness' }
        # node evaluates that to REAL's type. One readable token is not one answer when
        # something unreadable sits beside it.
        return None
    answers, unreadable = _types_in(source, call)
    if not answers and not unreadable:
        for argument in _split_arguments(call)[1:]:
            name = argument.strip()
            if not IDENT.fullmatch(name):
                continue
            for written in written_into(source, name):
                found, missing = _types_in(source, written)
                answers |= found
                unreadable = unreadable or missing
    if unreadable or len(answers) != 1:
        return None
    return answers.pop()


def scan_is_stable(source: str) -> bool:
    """Whether this file reads the same under both regex-disambiguation rules.

    Not a proxy. The scanner's one genuine ambiguity is whether `/` after `)` or `]`
    divides or opens a regex, and a wrong guess desynchronises the rest of the file - both
    forms of that failure hid dispatches silently, which is the worst way for a check to
    fail. This runs the scan under both readings and compares what they enumerate, so the
    thing measured is the scan itself rather than a count that stands in for it.

    A substring-parity check was written for this first and withdrawn: it convicted a
    legal file whose two dispatches share one options `const`, because parity is a budget
    rather than an invariant. This can only report that a file's reading depends on a
    guess, which is exactly the condition worth refusing.
    """
    return agent_calls(source, False) == agent_calls(source, True)
