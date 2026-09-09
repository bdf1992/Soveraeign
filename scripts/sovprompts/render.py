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

from sovprompts.scan import _opens_regex, masked, regex_end

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
        if char == "`":
            # Refused rather than rendered. A template literal was collapsed to one
            # `<expr>`, so its text reached the evaluator and appeared in nothing either
            # grader reads: an independent reading delivered the package's own inversion
            # sentence inside one and every check passed. This module's own ceiling says
            # anything built another way is reported as unreadable rather than silently
            # passing, and this was the construction that made that false.
            raise Unreadable(
                "a template literal delivers text this reader cannot render, so what the "
                "evaluator receives is not what any rule reads")
        if char.isspace() or char == "+":
            index += 1
            continue
        if char == "(":
            # Read inside the group, not past it. A parenthesised concatenation was
            # consumed whole and emitted as one marker, so prose inside it was delivered
            # to the evaluator and appeared in nothing any grader read - and because both
            # the frame's rendering and the delivered text collapsed the same region the
            # same way, the identity comparison matched *because neither side could see
            # it*. An independent reading put a countermand and an agent result there in
            # four shapes. Everything delivered is now read; whether prose contradicts
            # itself is a separate question this package does not claim to answer.
            close = _balanced(source, index, "(", ")")
            if close == -1:
                raise Unreadable("a group opens and never closes in a prompt expression")
            inner = _literals(source[index + 1:close])
            if inner:
                out.append(inner)
                pending_expr = inner.endswith(EXPR)
            index = close + 1
            continue
        if char == "/" and _opens_regex(source, index):
            # Skipped by the mask's own rule, so both readers end the regex in the same
            # place. Falling into the depth scan below let `/'/.source` swallow the rest
            # of the expression, taking the literals after it out of the delivered text.
            index = regex_end(source, index)
            if not pending_expr:
                out.append(EXPR)
                pending_expr = True
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


#: The three ways this repository's workflows declare a named function, matched up to the
#: opening of the parameter list. The parameters are then balanced rather than matched,
#: because `[^)]*` fails on a default value containing parentheses - `built = (built || {})`
#: - and a frame this reader cannot find switches the frame rules off silently instead of
#: refusing. An independent reading found exactly that shape.
DECLARATIONS = (
    r"function\s+{name}\s*\(",
    r"\b(?:const|let|var)\s+{name}\s*=\s*(?:async\s+)?function\s*\*?\s*[A-Za-z_$\w]*\s*\(",
    r"\b(?:const|let|var)\s+{name}\s*=\s*(?:async\s+)?\(",
)


def _declaration(code: str, name: str) -> int:
    """Where `name`'s function body opens - the index of its `{` - or -1 if it has none."""
    for shape in DECLARATIONS:
        match = re.search(shape.format(name=re.escape(name)), code)
        if not match:
            continue
        close = _balanced(code, match.end() - 1, "(", ")")
        if close == -1:
            continue
        index = close + 1
        while index < len(code) and code[index].isspace():
            index += 1
        if code[index:index + 2] == "=>":
            index += 2
            while index < len(code) and code[index].isspace():
                index += 1
        if index < len(code) and code[index] == "{":
            return index
    return -1


def _balanced(code: str, start: int, opener: str, closer: str) -> int:
    """The index of the bracket closing the one that opens at `start`, or -1."""
    index, depth = start, 0
    while index < len(code):
        if code[index] == opener:
            depth += 1
        elif code[index] == closer:
            depth -= 1
            if depth == 0:
                return index
        index += 1
    return -1


#: `const { name } = expr` and `const [name] = expr`, either bracket. A block-scoped one of
#: these shadows a frame declared above it, and the shadow is what a call resolves to.
DESTRUCTURED = r"\b(?:const|let|var)\s*[{\[][^}\]]*\b%s\b[^}\]]*[}\]]\s*="


def _bindings_of(source: str, name: str) -> int:
    """How many times this source binds `name`: a declaration, a write or a destructuring.

    JavaScript resolves a call to the binding in force when it runs, and this reader reads
    text. `witnessFrame = function (...)` placed after the declaration, a second
    `function witnessFrame(...)` that hoisting prefers, and a block-scoped
    `const { witnessFrame } = ...` shadow all leave the original in the file as dead code
    that every frame rule grades while the evaluator receives the other one. Independent
    readings built all three, and `verify.py` stayed at exit 0 each time with the subject
    pin gone and the build report named the oracle.

    The package already refuses a twice-written binding - `calls._declared_type` refuses a
    name written twice and a duplicate `agentType` key, for this reason - and the rule had
    simply never been applied to the frame itself.
    """
    code = masked(source)
    escaped = re.escape(name)
    sites = {match.start() for match in re.finditer(rf"\bfunction\s+{escaped}\s*\(", code)}
    sites |= {match.start() for match in re.finditer(rf"\b{escaped}\s*=(?!=)", code)}
    # Built with %-substitution: Python 3.11 refuses a backslash inside an f-string
    # expression, and `ENGINEERING.md` pins 3.11 or newer.
    sites |= {match.start() for match in re.finditer(DESTRUCTURED % escaped, code)}
    return len(sites)


def declares(source: str, name: str) -> bool:
    """Whether this source declares a function called `name`, in any shape it can take.

    One answer for every caller. `audit` asked this with `"function witnessFrame(" in
    masked(source)` while this module already knew three declaration shapes, so a frame
    written `const witnessFrame = function (...)` made the frame rules skip and the
    identity rule switch itself off, and an independent reading found the asymmetry. Two
    graders answering one question differently is the shape of several defeats already in
    the corpus.
    """
    return _declaration(masked(source), name) != -1


def _body(source: str, name: str) -> str:
    """The source of one function, by brace balance rather than by a text marker.

    Balanced on the mask, so a `{` or `}` inside a string literal is not a brace. Scanning
    raw source made `'SCOPE{. Derive it'` truncate the function, which an independent
    reading used to reach a refusal this package had recorded as unreachable.
    """
    bound = _bindings_of(source, name)
    if bound > 1:
        raise Unreadable(
            f"{name} is bound {bound} times, so which function a call reaches is decided "
            "when it runs and not by the first declaration in the file")
    code = masked(source)
    brace = _declaration(code, name)
    if brace == -1:
        raise Unreadable(f"no function named {name!r}")
    close = _balanced(code, brace, "{", "}")
    if close == -1:
        raise Unreadable(f"{name} has no closing brace")
    return source[brace + 1:close]


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
