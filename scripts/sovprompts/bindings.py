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

A second reading then defeated the repair five more ways, and every one was the same
mistake: `roots()` looked only at declarations while the module already knew that a name
is written in several places. `written_into` is now the single answer to "what reaches
this name", and both readers use it. It covers declaration, bare reassignment without a
keyword, accumulation through `push`, destructuring, a function that returns the account,
and a parameter bound at its call site. Each of those six was an exit-0 defeat.

What it still does not read: a computed member (`obj[key]`), a name reaching a workflow
through `import`, and any construction a JavaScript engine would evaluate but this does
not. Stated rather than implied, because the previous statement of this module's ceiling
was itself wrong.
"""

from __future__ import annotations

from functools import lru_cache
import re

IDENT = re.compile(r"[A-Za-z_$][\w$]*")
MEMBER = re.compile(r"\.\s*[A-Za-z_$][\w$]*")
#: Words that read as identifiers and bind nothing a builder's account could hide behind.
NOT_A_BINDING = frozenset({
    "await", "new", "typeof", "this", "true", "false", "null", "undefined", "void",
    "function", "return", "if", "else", "for", "while", "const", "let", "var",
})
AGENT_CALL = re.compile(r"\bagent\s*\(")
#: `const { name } = expr` and `const [name] = expr`, either bracket.
DESTRUCTURING = r"\b(?:const|let|var)\s*[{\[][^}\]]*\b%s\b[^}\]]*[}\]]\s*=\s*"
#: Continuation shapes. A statement runs on when its line ends on one of these, or when
#: the next line opens on one; reading only the first truncated most prompts in this tree.
ENDS_OPEN = ("+", "?", ":", "&&", "||", ",", "=", "(", "[")
OPENS_OPEN = ("+", "?", ":", ".", "&&", "||")


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


def _statement(source: str, start: int) -> str:
    """The expression beginning at `start`, read to the end of its statement."""
    index, depth, quote = start, 0, ""
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
            ends = source[start:index].rstrip().endswith(ENDS_OPEN)
            if not ends and not source[index + 1:].lstrip().startswith(OPENS_OPEN):
                break
        index += 1
    return source[start:index]


def _balanced(source: str, open_at: int) -> str:
    """The text inside the bracket that opens at `open_at`."""
    index, depth = open_at, 0
    while index < len(source):
        if source[index] in "([{":
            depth += 1
        elif source[index] in ")]}":
            depth -= 1
            if depth == 0:
                return source[open_at + 1:index]
        index += 1
    return ""


@lru_cache(maxsize=None)
def _function_body(source: str, name: str) -> str | None:
    """The body of `function NAME(...) { ... }`, so a helper cannot launder the account.

    `function accountText() { return built.summary }` spliced ahead of the frame was an
    exit-0 defeat: the name resolved to no declaration, so the reader treated it as a
    terminal that carried nothing.
    """
    match = re.search(rf"\bfunction\s+{re.escape(name)}\s*\(", source)
    if not match:
        return None
    brace = source.find("{", match.end())
    return _balanced(source, brace) if brace != -1 else None


@lru_cache(maxsize=None)
def _parameter_arguments(source: str, name: str) -> tuple[str, ...]:
    """Every argument passed where `name` is a function's parameter.

    A prompt built inside `function probePrompt(c)` carries whatever the call site hands
    it. `sov-review.js` and `sov-baseline.js` both reach a witness this way, and both read
    as carrying nothing while the account arrived as a parameter.
    """
    out: list[str] = []
    for match in re.finditer(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", source):
        parameters = [p.strip() for p in _balanced(source, match.end() - 1).split(",")]
        if name not in parameters:
            continue
        position = parameters.index(name)
        for call in re.finditer(rf"\b{re.escape(match.group(1))}\s*\(", source):
            arguments = _split_arguments(_balanced(source, call.end() - 1))
            if position < len(arguments):
                out.append(arguments[position])
    return tuple(out)


ITERATOR = "map|forEach|filter|flatMap|find|some|every|reduce"


@lru_cache(maxsize=None)
def _iterated_over(source: str, name: str) -> tuple[str, ...]:
    """The collection whose elements a callback or `for ... of` binds to `name`.

    `sov-review.js` reaches a witness with `findings.map(function (f) { ... f.summary ... })`
    and read as carrying nothing, because `f` is bound by a callback rather than declared
    or passed to a named function. The element carries whatever the collection carries.
    """
    out: list[str] = []
    receiver = r"([A-Za-z_$][\w$]*(?:\s*\.\s*[A-Za-z_$][\w$]*)*)"
    for pattern in (
        rf"{receiver}\s*\.\s*(?:{ITERATOR})\s*\(\s*function\s*\(\s*{re.escape(name)}\b",
        rf"{receiver}\s*\.\s*(?:{ITERATOR})\s*\(\s*\(?\s*{re.escape(name)}\s*\)?\s*=>",
    ):
        out.extend(match.group(1) for match in re.finditer(pattern, source))
    for match in re.finditer(
            rf"\bfor\s*\(\s*(?:const|let|var)\s+{re.escape(name)}\s+of\s+([^)]+)\)", source):
        out.append(match.group(1).strip())
    return tuple(out)


def _split_arguments(text: str) -> list[str]:
    """Split an argument list on its top-level commas."""
    out, depth, quote, start = [], 0, "", 0
    for index, char in enumerate(text):
        if quote:
            if char == quote and text[index - 1:index] != "\\":
                quote = ""
            continue
        if char in "'\"`":
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            out.append(text[start:index].strip())
            start = index + 1
    out.append(text[start:].strip())
    return [piece for piece in out if piece]


@lru_cache(maxsize=None)
def written_into(source: str, name: str) -> tuple[str, ...]:
    """Every expression that reaches a binding, by any route this reader understands.

    One answer for both readers below. Splitting it was how five defeats got through:
    `roots()` consulted declarations only, while the accumulator case was already handled
    a few lines away and never called.
    """
    out: list[str] = []
    escaped = re.escape(name)
    patterns = (
        rf"\b(?:const|let|var)\s+{escaped}\s*=\s*",              # declaration
        rf"\b{escaped}\s*=(?!=)\s*",                             # reassignment, no keyword
        rf"\b{escaped}\s*\.\s*(?:push|unshift|concat)\s*\(",     # accumulation
        # Built with %-substitution rather than an f-string: Python 3.11 refuses a
        # backslash inside an f-string expression, and ENGINEERING.md pins 3.11 or newer.
        DESTRUCTURING % escaped,
    )
    for pattern in patterns:
        for match in re.finditer(pattern, source):
            out.append(_statement(source, match.end()))
    body = _function_body(source, name)
    if body is not None:
        out.append(body)
    out.extend(_parameter_arguments(source, name))
    out.extend(_iterated_over(source, name))
    # A tuple because this is cached: a list would let one caller's edit reach the next.
    return tuple(out)


def _names(expr: str) -> list[str]:
    """The identifiers an expression mentions, with strings and member names removed."""
    return IDENT.findall(MEMBER.sub("", _without_strings(expr)))


def roots(source: str, expr: str, terminals: frozenset[str] = frozenset(),
          seen: frozenset[str] = frozenset()) -> set[str]:
    """The bindings an expression ultimately derives from.

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
    for name in _names(expr):
        if name in NOT_A_BINDING or name in seen:
            continue
        if name in terminals:
            # A name the caller is asking about is an answer, not something to resolve
            # through. Resolving `plan` into the schema that declares it would lose the
            # very binding the question is about.
            out.add(name)
            continue
        written = written_into(source, name)
        if not written:
            out.add(name)
            continue
        for expression in written:
            out |= roots(source, expression, terminals, seen | {name})
    return out


def derives_from_agent_result(source: str, expr: str,
                              seen: frozenset[str] = frozenset()) -> bool:
    """Whether an expression carries something an earlier `agent(...)` call produced.

    This is what "the builder's account" means mechanically: text a previous agent in the
    workflow returned. Naming the accounts instead - matching the tokens `claims`,
    `claimed`, `built` - is a substring heuristic wearing a list, and it missed
    `sov-librarian.js`, which splices a binding it calls `curated`, and two files whose
    account arrives as a function parameter. Every workflow is free to name its own
    bindings; none is free to hand an evaluator an agent's output as its oracle.
    """
    if AGENT_CALL.search(_without_strings(expr)):
        return True
    for name in _names(expr):
        if name in NOT_A_BINDING or name in seen:
            continue
        for written in written_into(source, name):
            if AGENT_CALL.search(_without_strings(written)):
                return True
            if derives_from_agent_result(source, written, seen | {name}):
                return True
    return False
