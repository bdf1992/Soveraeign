"""Resolve what a name in a workflow carries, and where that content came from.

Split from `dispatch.py` at the line ceiling `ENGINEERING.md` sets, along a boundary that
was already there: that module asks which prompts exist and what they splice in, this one
asks what a spliced name actually holds. Both readings are needed to grade the rule that
an evaluator never receives the builder's account as its oracle, and each was defeated
once by answering the question the other owns.

Everything here follows bindings rather than matching names. A check that bans the literal
text `built.` is defeated by `const acct = built`, and a check that lists the account
names - `claims`, `claimed`, `built` - misses a workflow that calls its own `curated`.
Both defeats were found by an independent reading of the first form of this code.
"""

from __future__ import annotations

import re

IDENT = re.compile(r"[A-Za-z_$][\w$]*")
MEMBER = re.compile(r"\.\s*[A-Za-z_$][\w$]*")
#: Words that read as identifiers and bind nothing a builder's account could hide behind.
NOT_A_BINDING = frozenset({
    "await", "new", "typeof", "this", "true", "false", "null", "undefined", "void",
})


def _without_strings(expr: str) -> str:
    """The expression with its string literals removed, so prose is not read as code.

    Without this, resolving `plan.operation` walks into the prose of every prompt the
    binding chain touches and returns several hundred English words as bindings.
    """
    out: list[str] = []
    index, length = 0, len(expr)
    while index < length:
        char = expr[index]
        if char in "'\"`":
            quote, index = char, index + 1
            while index < length and expr[index] != quote:
                index += 2 if expr[index] == "\\" else 1
            index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _initialiser(source: str, name: str) -> str | None:
    """The right-hand side of `const|let|var NAME = ...`, read to the end of that statement.

    Bracket- and quote-aware, and it treats a newline as the end of the statement only
    when the line does not end on an operator, so a multi-line ternary or concatenation
    is read whole rather than truncated at its first newline.
    """
    match = re.search(rf"\b(?:const|let|var)\s+{re.escape(name)}\s*=\s*", source)
    if not match:
        return None
    start = index = match.end()
    depth, quote = 0, ""
    while index < len(source):
        char = source[index]
        if quote:
            if char == "\\":
                index += 2
                continue
            if char == quote:
                quote = ""
            index += 1
            continue
        if char in "'\"`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                break
            depth -= 1
        elif char == "\n" and depth == 0:
            # A statement continues when this line ends on an operator or the next line
            # opens on one. Reading only the trailing form truncated every prompt in this
            # repository written in the leading-`+` style, which is most of them, and a
            # truncated prompt silently drops out of the label check.
            ends_open = source[start:index].rstrip().endswith(
                ("+", "?", ":", "&&", "||", ",", "=", "(", "["))
            nxt = source[index + 1:].lstrip()
            if not ends_open and not nxt.startswith(("+", "?", ":", ".", "&&", "||")):
                break
        index += 1
    return source[start:index]


def roots(source: str, expr: str, terminals: frozenset[str] = frozenset(),
          seen: frozenset[str] = frozenset()) -> set[str]:
    """The bindings an expression ultimately derives from, following `const` aliases.

    `const acct = built` followed by `acct.summary` resolves to `{'built'}`. Banning the
    literal text `built.` instead is defeated by that one line, and an independent reading
    defeated the literal form exactly that way. A check that reads a name where it could
    follow a binding is the defect this module exists to refuse, so it is not repeated
    here.

    Member names are stripped before identifiers are read, so `x.built` resolves to `x`
    and not to a property that happens to share a binding's name. Recursion carries the
    names already visited, so a cyclic or self-referential binding terminates.
    """
    out: set[str] = set()
    for name in IDENT.findall(MEMBER.sub("", _without_strings(expr))):
        if name in NOT_A_BINDING or name in seen:
            continue
        if name in terminals:
            # A name the caller is asking about is an answer, not something to resolve
            # through. Resolving `plan` into the schema that declares it would lose the
            # very binding the question is about.
            out.add(name)
            continue
        initialiser = _initialiser(source, name)
        if initialiser is None:
            out.add(name)
            continue
        out |= roots(source, initialiser, terminals, seen | {name})
    return out


AGENT_CALL = re.compile(r"\bagent\s*\(")


def derives_from_agent_result(source: str, expr: str, seen: frozenset[str] = frozenset()) -> bool:
    """Whether an expression carries something an earlier `agent(...)` call produced.

    This is what "the builder's account" means mechanically: text a previous agent in the
    workflow returned. Naming the accounts instead - matching the tokens `claims`,
    `claimed`, `built` - is a substring heuristic wearing a list, and it missed
    `sov-librarian.js`, which splices a binding it calls `curated` and a survey result,
    and carried no label at all. Every workflow is free to name its own bindings; none is
    free to hand an evaluator an agent's output as its oracle.
    """
    for name in IDENT.findall(MEMBER.sub("", _without_strings(expr))):
        if name in NOT_A_BINDING or name in seen:
            continue
        for written in _written_into(source, name):
            if AGENT_CALL.search(_without_strings(written)):
                return True
            if derives_from_agent_result(source, written, seen | {name}):
                return True
    return False


def _written_into(source: str, name: str) -> list[str]:
    """Every expression written into a binding: its initialiser, reassignments, and pushes.

    An accumulator defeats initialiser-only resolution. `sov-asset.js` and
    `sov-byom.js` both declare `let built = []` and push agent results into it later, so
    following only `= []` says the binding carries nothing and both files' witness
    prompts drop out of the rule while handing over exactly what it governs.
    """
    out: list[str] = []
    initialiser = _initialiser(source, name)
    if initialiser is not None:
        out.append(initialiser)
    for match in re.finditer(
            rf"\b{re.escape(name)}\s*(?:\.\s*(?:push|unshift|concat)\s*\(|=(?!=))", source):
        index, depth, quote, start = match.end(), 0, "", match.end()
        while index < len(source):
            char = source[index]
            if quote:
                index += 2 if char == "\\" else 1
                if index <= len(source) and source[index - 1:index] == quote:
                    quote = ""
                continue
            if char in "'\"`":
                quote = char
            elif char in "([{":
                depth += 1
            elif char in ")]}":
                if depth == 0:
                    break
                depth -= 1
            elif char == "\n" and depth == 0:
                break
            index += 1
        out.append(source[start:index])
    return out
