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

from sovprompts.names import _after, agent_call_pattern
from sovprompts.scan import _balanced, _statement, masked

IDENT = re.compile(r"[A-Za-z_$][\w$]*")
MEMBER = re.compile(r"\.\s*[A-Za-z_$][\w$]*")
#: Words that read as identifiers and bind nothing a builder's account could hide behind.
NOT_A_BINDING = frozenset({
    "await", "new", "typeof", "this", "true", "false", "null", "undefined", "void",
    "function", "return", "if", "else", "for", "while", "const", "let", "var",
})
#: `const { name } = expr` and `const [name] = expr`, either bracket.
DESTRUCTURING = r"\b(?:const|let|var)\s*[{\[][^}\]]*\b%s\b[^}\]]*[}\]]\s*=(?!=)"


def _without_strings(expr: str) -> str:
    """The expression with everything that is not code blanked, via the one mask.

    This used to be a private scanner that stripped string literals and nothing else. It
    left comments intact, so a comment holding `witnessFrame(` removed a dispatch from the
    repo-wide rule, and it discarded whole template literals including their
    interpolations, so `` `${built.summary}` `` resolved to nothing. Both were found by a
    reader that had seen none of the earlier work, and both were the package holding
    several scanners that disagreed rather than one that did not.
    """
    return masked(expr)


def _inside(source: str, open_at: int) -> str:
    """The text inside the bracket that opens at `open_at`, through the one balancer.

    This module used to carry its own bracket scan, on raw source, counting every kind of
    bracket together. Five readings have defeated this package at a place where two
    readers answered one question differently, so the question is asked in one place.
    """
    close = _balanced(masked(source), open_at, source[open_at], {"(": ")", "[": "]", "{": "}"}[source[open_at]])
    return source[open_at + 1:close] if close != -1 else ""


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
    return _inside(source, brace) if brace != -1 else None


@lru_cache(maxsize=None)
def _parameter_arguments(source: str, name: str) -> tuple[str, ...]:
    """Every argument passed where `name` is a function's parameter.

    A prompt built inside `function probePrompt(c)` carries whatever the call site hands
    it. `sov-review.js` and `sov-baseline.js` both reach a witness this way, and both read
    as carrying nothing while the account arrived as a parameter.
    """
    out: list[str] = []
    for match in re.finditer(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\(", source):
        parameters = [p.strip() for p in _inside(source, match.end() - 1).split(",")]
        if name not in parameters:
            continue
        position = parameters.index(name)
        for call in re.finditer(rf"\b{re.escape(match.group(1))}\s*\(", source):
            arguments = _split_arguments(_inside(source, call.end() - 1))
            if position < len(arguments):
                out.append(arguments[position])
    return tuple(out)


ITERATOR = "map|forEach|filter|flatMap|find|some|every|reduce"
#: The callback's first parameter, after the iterator method. The receiver is read
#: backwards from the dot rather than captured, because a pattern matching a dotted
#: receiver ahead of this backtracks catastrophically: it was 73% of the time spent
#: grading one workflow, and the defeats corpus multiplied that by twenty-nine.
CALLBACK = re.compile(
    rf"\.\s*(?:{ITERATOR})\s*\(\s*(?:function\s*)?\(?\s*([A-Za-z_$][\w$]*)")
FOR_OF = re.compile(r"\bfor\s*\(\s*(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s+of\s+([^)]+)\)")


def _receiver_before(source: str, dot: int) -> str:
    """The dotted expression ending at `dot`, read backwards."""
    index = dot
    while index > 0 and (source[index - 1].isalnum() or source[index - 1] in "_$. \t"):
        index -= 1
    return source[index:dot].strip()


@lru_cache(maxsize=None)
def _iteration_map(source: str) -> dict[str, tuple[str, ...]]:
    """Each callback or `for ... of` parameter mapped to what it iterates over.

    `sov-review.js` reaches a witness with `findings.map(function (f) { ... f.summary })`
    and read as carrying nothing, because `f` is bound by a callback rather than declared.
    The element carries whatever the collection carries.
    """
    out: dict[str, list[str]] = {}
    for match in CALLBACK.finditer(source):
        receiver = _receiver_before(source, match.start())
        if receiver:
            out.setdefault(match.group(1), []).append(receiver)
    for match in FOR_OF.finditer(source):
        out.setdefault(match.group(1), []).append(match.group(2).strip())
    return {name: tuple(items) for name, items in out.items()}


def _iterated_over(source: str, name: str) -> tuple[str, ...]:
    """The collection whose elements a callback or `for ... of` binds to `name`."""
    return _iteration_map(source).get(name, ())


def _split_arguments(text: str) -> list[str]:
    """Split an argument list on its top-level commas, found on the one mask.

    On `masked(text)` rather than on a scan of this module's own. A comma inside a comment
    or a regex is not a separator, and an unbalanced `{` inside a comment - `/* { */` -
    made a two-argument dispatch read as one, which took its prompt out of every rule.
    `masked` preserves length, so every offset below is valid in `text` itself.
    """
    code = masked(text)
    out, depth, start = [], 0, 0
    for index, char in enumerate(code):
        if char in "([{":
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
        rf"\b(?:const|let|var)\s+{escaped}\s*=(?!=)",              # declaration
        rf"\b{escaped}\s*=(?!=)",                                 # reassignment, no keyword
        rf"\b{escaped}\s*\.\s*(?:push|unshift|concat)\s*\(",     # accumulation
        rf"\b{escaped}\s*\.\s*[A-Za-z_$][\w$]*\s*=(?!=)",         # member write
        rf"\b{escaped}\s*\[[^\]]*\]\s*=(?!=)",                    # indexed write
        rf"\bObject\s*\.\s*assign\s*\(\s*{escaped}\s*,",           # merged in
        # Built with %-substitution rather than an f-string: Python 3.11 refuses a
        # backslash inside an f-string expression, and ENGINEERING.md pins 3.11 or newer.
        DESTRUCTURING % escaped,
    )
    # Searched on the mask and read from the source, the way every other reader in this
    # package works. Searching the raw source made a comment holding `x =` a binding, and
    # made this module and `names.writes_by_name` answer the same question differently for
    # a hundred and forty-six names.
    code = masked(source)
    for pattern in patterns:
        for match in re.finditer(pattern, code):
            out.append(_statement(source, _after(source, match.end())))
    body = _function_body(source, name)
    if body is not None:
        out.append(body)
    out.extend(_parameter_arguments(source, name))
    out.extend(_iterated_over(source, name))
    # Deduplicated: a `const x = await agent(...)` matches both the declaration and the
    # reassignment pattern on the same `=`, and resolving the identical text twice is
    # work without an answer. A tuple because this is cached, so a list would let one
    # caller's edit reach the next.
    return tuple(dict.fromkeys(out))


#: An object-literal key: an identifier in the position right after `{` or `,` and right
#: before `:`. Blanked before identifiers are read, because a key is not a reference.
OBJECT_KEY = re.compile(r"([{,]\s*)[A-Za-z_$][\w$]*(\s*:)")


def _names(expr: str) -> list[str]:
    """The identifiers an expression mentions, with strings, members and keys removed.

    Keys as well as member names. A JSON Schema is an object literal whose keys are the
    domain's own words - `summary`, `residuals`, `verdicts` - and reading them as
    references walked `BUILD_SCHEMA` through a workflow's `residuals` binding to the
    witness dispatch itself. An independent reading measured that on the pristine tree:
    three schema constants resolved to "derives from an agent result", so the refusals
    annotated "provenance to an agent result is measurable" were name collisions.
    Convicting correct code is the failure this package holds itself to avoiding.
    """
    code = OBJECT_KEY.sub(lambda m: m.group(1) + " " * (m.end() - m.start()
                                                        - len(m.group(1)) - len(m.group(2)))
                          + m.group(2), _without_strings(expr))
    return IDENT.findall(MEMBER.sub("", code))


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
    reaches_agent = agent_call_pattern(source)
    if reaches_agent.search(_without_strings(expr)):
        return True
    for name in _names(expr):
        if name in NOT_A_BINDING or name in seen:
            continue
        for written in written_into(source, name):
            if reaches_agent.search(_without_strings(written)):
                return True
            if derives_from_agent_result(source, written, seen | {name}):
                return True
    return False
